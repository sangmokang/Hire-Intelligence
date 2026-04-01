from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from supabase import Client

from app.database import get_db
from app.dependencies import get_current_user, get_supabase_client
from app.middleware.plan_access import require_plan
from app.schemas.user import (
    UserProfileResponse,
    UserProfileUpdate,
    PasswordChangeRequest,
    NotificationPreferences,
    UsageStats,
    DeleteAccountRequest,
)
from app.schemas.common import ApiResponse
from app.services.user_service import UserService
from app.services.report_service import report_service
from app.middleware.usage_tracker import get_buffered_stats

router = APIRouter(prefix="/me", tags=["me"])


def _profile_to_response(profile, email: str | None = None) -> UserProfileResponse:
    return UserProfileResponse(
        id=str(profile.id),
        email=email,
        name=profile.name,
        phone=profile.phone,
        company=profile.company,
        job_title=profile.job_title,
        profile_image_url=profile.profile_image_url,
        role=profile.role,
        category=profile.category,
        status=profile.status,
        organization_id=str(profile.organization_id) if profile.organization_id else None,
        last_login_at=profile.last_login_at,
        login_count=profile.login_count,
        created_at=profile.created_at,
    )


@router.get("", response_model=ApiResponse[UserProfileResponse])
async def get_my_profile(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """내 프로필 조회"""
    service = UserService(db)
    profile = service.get_profile(current_user["id"])
    if not profile:
        # Return minimal profile from JWT if no DB record yet
        return ApiResponse(
            data=UserProfileResponse(
                id=current_user["id"],
                email=current_user.get("email"),
            )
        )
    return ApiResponse(data=_profile_to_response(profile, current_user.get("email")))


@router.patch("", response_model=ApiResponse[UserProfileResponse])
async def update_my_profile(
    body: UserProfileUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """내 프로필 업데이트"""
    service = UserService(db)
    update_data = body.model_dump(exclude_none=True)
    profile = service.update_profile(current_user["id"], update_data)
    if not profile:
        raise HTTPException(status_code=404, detail="프로필을 찾을 수 없습니다.")
    return ApiResponse(
        data=_profile_to_response(profile, current_user.get("email")),
        message="프로필이 업데이트되었습니다.",
    )


@router.post("/password", response_model=ApiResponse[None])
async def change_password(
    body: PasswordChangeRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    supabase: Client = Depends(get_supabase_client),
):
    """비밀번호 변경"""
    service = UserService(db, supabase)
    await service.change_password(
        user_id=current_user["id"],
        email=current_user["email"],
        current_password=body.current_password,
        new_password=body.new_password,
    )
    return ApiResponse(message="비밀번호가 변경되었습니다.")


@router.get("/notifications", response_model=ApiResponse[dict])
async def get_notifications(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """알림 설정 조회"""
    service = UserService(db)
    prefs = service.get_notification_preferences(current_user["id"])
    return ApiResponse(data=prefs)


@router.patch("/notifications", response_model=ApiResponse[dict])
async def update_notifications(
    body: NotificationPreferences,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """알림 설정 업데이트 (부분 업데이트 지원)"""
    service = UserService(db)
    # None 값 제외한 변경 항목만 전달
    prefs = body.model_dump(exclude_none=True)
    updated = service.update_notification_preferences(current_user["id"], prefs)
    return ApiResponse(data=updated, message="알림 설정이 업데이트되었습니다.")


@router.delete("", response_model=ApiResponse[None])
async def delete_account(
    body: DeleteAccountRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    supabase: Client = Depends(get_supabase_client),
):
    """계정 삭제 (비밀번호 검증 후 소프트 삭제 + Supabase 세션 무효화)"""
    from app.dependencies import get_supabase_anon_client

    # 현재 비밀번호 검증
    anon = get_supabase_anon_client()
    try:
        anon.auth.sign_in_with_password({
            "email": current_user["email"],
            "password": body.current_password,
        })
    except Exception:
        raise HTTPException(status_code=401, detail="비밀번호가 올바르지 않습니다")

    service = UserService(db, supabase)
    await service.delete_account(current_user["id"])
    return ApiResponse(message="계정이 삭제되었습니다.")


@router.get("/usage", response_model=ApiResponse[UsageStats])
async def get_usage(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """사용량 통계 조회 (최근 30일) — DB 데이터 + 인메모리 버퍼 머지"""
    service = UserService(db)
    stats = service.get_usage_stats(current_user["id"])

    # 인메모리 버퍼에서 아직 flush되지 않은 데이터 머지
    buf = get_buffered_stats(str(current_user["id"]))
    merged_daily = dict(stats.get("daily_api_calls", {}))
    for date_str, count in buf.get("daily_api_calls", {}).items():
        merged_daily[date_str] = merged_daily.get(date_str, 0) + count
    merged_views = dict(stats.get("view_access", {}))
    for view_name, count in buf.get("view_access", {}).items():
        merged_views[view_name] = merged_views.get(view_name, 0) + count

    return ApiResponse(data=UsageStats(daily_api_calls=merged_daily, view_access=merged_views))


@router.get("/report/preview", response_class=HTMLResponse)
async def preview_weekly_report(
    current_user: dict = Depends(require_plan("PRO")),
    db: Session = Depends(get_db),
):
    """주간 리포트 HTML 미리보기 (PRO 이상)."""
    data = report_service.get_report_data(db)
    html = report_service.generate_weekly_report_html(data)
    return HTMLResponse(content=html)
