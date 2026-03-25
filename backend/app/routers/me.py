from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.schemas.user import UserProfileResponse, UserProfileUpdate
from app.schemas.common import ApiResponse
from app.services.user_service import UserService

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
    profile = await service.get_profile(current_user["id"])
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
    profile = await service.update_profile(current_user["id"], update_data)
    if not profile:
        raise HTTPException(status_code=404, detail="프로필을 찾을 수 없습니다.")
    return ApiResponse(
        data=_profile_to_response(profile, current_user.get("email")),
        message="프로필이 업데이트되었습니다.",
    )
