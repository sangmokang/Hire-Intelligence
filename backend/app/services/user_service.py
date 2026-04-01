import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from supabase import Client

from app.models.user import UserProfile, UserRole, UserStatus


class UserService:
    def __init__(self, db: Session, supabase: Client | None = None):
        self.db = db
        self.supabase = supabase

    def get_profile(self, user_id: str) -> UserProfile | None:
        """사용자 프로필 조회"""

        try:
            uid = uuid.UUID(user_id)
        except ValueError:
            return None
        return self.db.query(UserProfile).filter(UserProfile.id == uid).first()

    def update_profile(self, user_id: str, data: dict) -> UserProfile | None:
        """사용자 프로필 업데이트"""

        try:
            uid = uuid.UUID(user_id)
        except ValueError:
            return None

        profile = self.db.query(UserProfile).filter(UserProfile.id == uid).first()
        if not profile:
            return None

        allowed_fields = {"name", "phone", "company", "job_title", "profile_image_url", "category"}
        for key, value in data.items():
            if key in allowed_fields and value is not None:
                setattr(profile, key, value)

        profile.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(profile)
        return profile

    def upsert_on_login(
        self, user_id: str, email: str, provider: str, metadata: dict
    ) -> UserProfile:
        """로그인 시 프로필 생성 또는 업데이트 (첫 Google OAuth 사용자)"""

        try:
            uid = uuid.UUID(user_id)
        except ValueError:
            raise ValueError(f"Invalid user_id UUID: {user_id}")

        profile = self.db.query(UserProfile).filter(UserProfile.id == uid).first()
        now = datetime.now(timezone.utc)

        if profile is None:
            profile = UserProfile(
                id=uid,
                name=metadata.get("full_name") or metadata.get("name"),
                profile_image_url=metadata.get("avatar_url"),
                auth_provider=provider,
                role=UserRole.USER,
                status=UserStatus.ACTIVE,
                login_count=1,
                last_login_at=now,
            )
            self.db.add(profile)
        else:
            profile.auth_provider = provider
            profile.login_count = (profile.login_count or 0) + 1
            profile.last_login_at = now
            profile.updated_at = now

        self.db.commit()
        self.db.refresh(profile)
        return profile

    async def change_password(
        self, user_id: str, email: str, current_password: str, new_password: str
    ) -> None:
        """비밀번호 변경: 현재 비밀번호 검증 후 service role로 새 비밀번호 설정"""
        if self.supabase is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Supabase 클라이언트가 초기화되지 않았습니다.",
            )
        # 현재 비밀번호 검증 (anon 클라이언트로 sign_in 시도)
        try:
            from app.dependencies import get_supabase_anon_client
            anon_client = get_supabase_anon_client()
            anon_client.auth.sign_in_with_password({"email": email, "password": current_password})
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="현재 비밀번호가 올바르지 않습니다.",
            )
        # service role로 새 비밀번호 설정
        try:
            self.supabase.auth.admin.update_user_by_id(user_id, {"password": new_password})
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"비밀번호 변경에 실패했습니다: {str(e)}",
            )

    def get_notification_preferences(self, user_id: str) -> dict:
        """알림 설정 조회"""
        profile = self.get_profile(user_id)
        if not profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="프로필을 찾을 수 없습니다.")
        # 기본값 반환 (DB에 NULL인 경우)
        return profile.notification_preferences or {"weekly_report": True, "hiring_alert": True}

    def update_notification_preferences(self, user_id: str, prefs: dict) -> dict:
        """알림 설정 머지 업데이트 (전체 교체 아님)"""
        try:
            uid = uuid.UUID(user_id)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="프로필을 찾을 수 없습니다.")

        profile = self.db.query(UserProfile).filter(UserProfile.id == uid).first()
        if not profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="프로필을 찾을 수 없습니다.")

        # 기존 설정에 변경값 머지 (None 값 제외)
        current = profile.notification_preferences or {"weekly_report": True, "hiring_alert": True}
        merged = {**current, **{k: v for k, v in prefs.items() if v is not None}}
        profile.notification_preferences = merged
        profile.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(profile)
        return profile.notification_preferences

    async def delete_account(self, user_id: str) -> None:
        """계정 삭제: DB status DELETED 설정 + Supabase 세션 무효화(banned)"""
        if self.supabase is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Supabase 클라이언트가 초기화되지 않았습니다.",
            )
        try:
            uid = uuid.UUID(user_id)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="프로필을 찾을 수 없습니다.")

        profile = self.db.query(UserProfile).filter(UserProfile.id == uid).first()
        if not profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="프로필을 찾을 수 없습니다.")

        # DB에서 탈퇴 상태로 변경
        profile.status = UserStatus.DELETED
        profile.delete_requested_at = datetime.now(timezone.utc)
        profile.updated_at = datetime.now(timezone.utc)
        self.db.commit()

        # Supabase 세션 무효화 (banned 처리)
        try:
            self.supabase.auth.admin.update_user_by_id(user_id, {"ban_duration": "876600h"})
        except Exception as e:
            # 세션 무효화 실패는 로그만 남기고 계속 진행 (DB 변경은 이미 완료)
            import logging
            logging.getLogger(__name__).warning(f"Supabase ban 처리 실패 (user_id={user_id}): {e}")

    def get_usage_stats(self, user_id: str) -> dict:
        """사용량 통계 조회 (최근 30일 데이터)"""
        from datetime import timedelta
        profile = self.get_profile(user_id)
        if not profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="프로필을 찾을 수 없습니다.")

        raw_stats = profile.usage_stats or {}
        # 최근 30일 날짜 기준으로 daily_api_calls 필터링
        cutoff = datetime.now(timezone.utc).date() - timedelta(days=30)
        daily_api_calls = {
            date_str: count
            for date_str, count in raw_stats.get("daily_api_calls", {}).items()
            if date_str >= str(cutoff)
        }
        view_access = raw_stats.get("view_access", {})
        return {"daily_api_calls": daily_api_calls, "view_access": view_access}
