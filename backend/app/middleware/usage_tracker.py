"""사용량 추적 미들웨어 — 인증된 사용자의 API 호출을 인메모리 카운터로 추적하고
5분마다 (또는 GET /me/usage 호출 시) user_profiles.usage_stats에 flush한다."""

import asyncio
import logging
from collections import defaultdict
from datetime import datetime, timezone

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)

# 인메모리 카운터: {user_id: {"daily_api_calls": {"2026-04-01": 3}, "view_access": {"top-companies": 5}}}
_usage_buffer: dict[str, dict] = defaultdict(lambda: {"daily_api_calls": {}, "view_access": {}})

# 뷰 경로 → 뷰 이름 매핑
_VIEW_PATH_MAP: dict[str, str] = {
    "/api/v1/dashboard/top-companies": "top-companies",
    "/api/v1/dashboard/sd-matrix": "sd-matrix",
    "/api/v1/dashboard/hiring-trends": "hiring-trends",
    "/api/v1/dashboard/resume-match": "resume-match",
    "/api/v1/dashboard/company-dna": "company-dna",
    "/api/v1/dashboard/jd-insights": "jd-insights",
}


def _today_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def record_api_call(user_id: str, path: str) -> None:
    """인메모리 버퍼에 API 호출 기록"""
    today = _today_str()
    buf = _usage_buffer[user_id]

    # 일별 호출 수 증가
    buf["daily_api_calls"][today] = buf["daily_api_calls"].get(today, 0) + 1

    # 뷰 접근 경로인 경우 view_access 카운터 증가
    view_name = _VIEW_PATH_MAP.get(path)
    if view_name:
        buf["view_access"][view_name] = buf["view_access"].get(view_name, 0) + 1


def get_buffered_stats(user_id: str) -> dict:
    """특정 사용자의 인메모리 버퍼 통계 반환"""
    return dict(_usage_buffer.get(user_id, {"daily_api_calls": {}, "view_access": {}}))


async def flush_to_db(user_id: str, db_session_factory) -> None:
    """인메모리 버퍼를 DB의 usage_stats에 머지하여 저장"""
    import uuid as _uuid
    from sqlalchemy.dialects.postgresql import insert as pg_insert

    buf = _usage_buffer.get(user_id)
    if not buf:
        return

    try:
        async with db_session_factory() as db:
            from app.models.user import UserProfile
            try:
                uid = _uuid.UUID(user_id)
            except ValueError:
                return

            profile = db.query(UserProfile).filter(UserProfile.id == uid).first()
            if not profile:
                return

            # 기존 DB 값과 머지
            existing = profile.usage_stats or {}
            existing_calls = existing.get("daily_api_calls", {})
            existing_views = existing.get("view_access", {})

            # 일별 호출수 머지 (누적 합산)
            for date_str, count in buf["daily_api_calls"].items():
                existing_calls[date_str] = existing_calls.get(date_str, 0) + count

            # 뷰 접근수 머지 (누적 합산)
            for view_name, count in buf["view_access"].items():
                existing_views[view_name] = existing_views.get(view_name, 0) + count

            profile.usage_stats = {
                "daily_api_calls": existing_calls,
                "view_access": existing_views,
            }
            db.commit()

            # 버퍼 초기화
            _usage_buffer[user_id] = {"daily_api_calls": {}, "view_access": {}}
    except Exception as e:
        logger.warning(f"usage_stats flush 실패 (user_id={user_id}): {e}")


class UsageTrackerMiddleware(BaseHTTPMiddleware):
    """인증된 사용자의 API 호출을 인메모리 카운터로 추적하는 미들웨어"""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        # 인증 실패(401/403) 또는 정적 리소스는 추적 제외
        if response.status_code in (401, 403):
            return response
        if request.url.path in ("/health", "/docs", "/redoc", "/openapi.json"):
            return response

        # request.state에 user_id가 있으면 기록 (get_current_user 이후 설정 가능)
        user_id: str | None = getattr(request.state, "user_id", None)
        if user_id:
            record_api_call(user_id, request.url.path)

        return response
