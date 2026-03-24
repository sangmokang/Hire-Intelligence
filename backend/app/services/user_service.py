from fastapi import HTTPException


class UserService:
    """사용자 관련 비즈니스 로직"""

    async def get_profile(self, user_id: str) -> dict:
        """사용자 프로필 조회 (DB 연동 전 stub)"""
        # TODO: DB 연동 후 실제 구현
        return {
            "id": user_id,
            "role": "USER",
            "status": "ACTIVE",
            "login_count": 0,
        }

    async def update_profile(self, user_id: str, data: dict) -> dict:
        """사용자 프로필 업데이트 (DB 연동 전 stub)"""
        # TODO: DB 연동 후 실제 구현
        return {"id": user_id, **data}
