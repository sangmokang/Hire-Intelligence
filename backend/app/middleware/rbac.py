from fastapi import Depends, HTTPException, status
from app.dependencies import get_current_user

# 역할 레벨 정의
ROLE_LEVELS: dict[str, int] = {
    "SUPER_ADMIN": 100,
    "USER": 10,
    "GUEST": 0,
}


def require_role(required_role: str):
    """역할 기반 접근 제어 의존성"""
    async def dependency(current_user: dict = Depends(get_current_user)) -> dict:
        user_role = current_user.get("role", "USER")
        user_level = ROLE_LEVELS.get(user_role, 0)
        required_level = ROLE_LEVELS.get(required_role, 0)

        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"권한이 부족합니다. '{required_role}' 이상의 권한이 필요합니다.",
            )
        return current_user

    return dependency


# 편의 의존성
require_super_admin = require_role("SUPER_ADMIN")
require_user = require_role("USER")
