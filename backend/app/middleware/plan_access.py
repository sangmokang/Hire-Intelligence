"""플랜별 접근 제어 미들웨어"""
from fastapi import Depends, HTTPException, status
from app.dependencies import get_current_user

# 플랜 레벨 정의 (숫자가 높을수록 상위 플랜)
PLAN_LEVELS: dict[str, int] = {
    "STARTER": 0,
    "PRO": 1,
    "ENTERPRISE": 2,
}

# 플랜별 접근 가능한 뷰 정의
PLAN_VIEWS: dict[str, set[str] | None] = {
    "STARTER": {"sd-matrix", "top-companies"},
    "PRO": {"sd-matrix", "top-companies", "timeline", "trends", "resume-match", "company-analysis", "jd-insights", "company-dna", "segment-benchmark"},
    "ENTERPRISE": None,  # None = 모든 뷰 접근 가능
}


def require_plan(min_plan: str):
    """최소 플랜 요구사항 검사 의존성 팩토리"""
    min_level = PLAN_LEVELS.get(min_plan, 0)

    def dependency(current_user: dict = Depends(get_current_user)) -> dict:
        user_plan = current_user.get("plan", "STARTER")
        user_level = PLAN_LEVELS.get(user_plan, 0)

        if user_level < min_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"{min_plan} 플랜 이상에서 사용 가능합니다. 현재 플랜: {user_plan}",
            )
        return current_user

    return dependency


# 편의 의존성
require_pro = require_plan("PRO")
require_enterprise = require_plan("ENTERPRISE")
