from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_current_user
from app.schemas.user import UserProfileResponse, UserProfileUpdate
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/me", tags=["me"])


@router.get("", response_model=ApiResponse[UserProfileResponse])
async def get_my_profile(current_user: dict = Depends(get_current_user)):
    """내 프로필 조회"""
    return ApiResponse(
        data=UserProfileResponse(
            id=current_user["id"],
            email=current_user["email"],
        )
    )


@router.patch("", response_model=ApiResponse[UserProfileResponse])
async def update_my_profile(
    body: UserProfileUpdate,
    current_user: dict = Depends(get_current_user),
):
    """내 프로필 업데이트"""
    # TODO: DB 연동 후 실제 업데이트 구현
    return ApiResponse(
        data=UserProfileResponse(
            id=current_user["id"],
            email=current_user["email"],
            name=body.name,
            phone=body.phone,
            company=body.company,
            job_title=body.job_title,
            profile_image_url=body.profile_image_url,
            category=body.category,
        ),
        message="프로필이 업데이트되었습니다.",
    )
