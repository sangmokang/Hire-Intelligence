import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.user import UserProfile, UserRole, UserStatus


class UserService:
    def __init__(self, db: Session):
        self.db = db

    async def get_profile(self, user_id: str) -> UserProfile | None:
        """사용자 프로필 조회"""

        try:
            uid = uuid.UUID(user_id)
        except ValueError:
            return None
        return self.db.query(UserProfile).filter(UserProfile.id == uid).first()

    async def update_profile(self, user_id: str, data: dict) -> UserProfile | None:
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

    async def upsert_on_login(
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
