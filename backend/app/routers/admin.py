from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_current_user
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/admin", tags=["admin"])


def require_super_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """슈퍼 어드민 권한 확인"""
    # TODO: DB에서 실제 role 확인
    return current_user


@router.get("/users", response_model=ApiResponse[list])
async def list_users(current_user: dict = Depends(require_super_admin)):
    """전체 사용자 목록 (관리자 전용)"""
    # TODO: DB 연동 후 실제 구현
    return ApiResponse(data=[], message="사용자 목록")


@router.get("/stats", response_model=ApiResponse[dict])
async def get_stats(current_user: dict = Depends(require_super_admin)):
    """플랫폼 통계 (관리자 전용)"""
    return ApiResponse(
        data={
            "total_users": 0,
            "active_users": 0,
            "total_organizations": 0,
        }
    )
