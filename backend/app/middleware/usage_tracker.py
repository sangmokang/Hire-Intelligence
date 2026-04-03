"""사용량 추적 미들웨어 — 인증된 사용자의 API 호출을 인메모리 카운터로 추적하고
5분마다 (또는 GET /me/usage 호출 시) user_profiles.usage_stats에 flush한다."""

import logging
import threading
from collections import defaultdict
from datetime import datetime, timezone

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)

# 인메모리 카운터: {user_id: {"daily_api_calls": {"2026-04-01": 3}, "view_access": {"top-companies": 5}, "expert_panel_calls": {"2026-04-01": 1}}}
_usage_buffer: dict[str, dict] = defaultdict(
    lambda: {"daily_api_calls": {}, "view_access": {}, "expert_panel_calls": {}}
)

# 동시 접근 race condition 방지용 락
_buffer_lock = threading.Lock()

# 뷰 경로 → 뷰 이름 매핑
_VIEW_PATH_MAP: dict[str, str] = {
    "/api/v1/dashboard/top-companies": "top-companies",
    "/api/v1/dashboard/sd-matrix": "sd-matrix",
    "/api/v1/dashboard/hiring-trends": "hiring-trends",
    "/api/v1/dashboard/resume-match": "resume-match",
    "/api/v1/dashboard/company-dna": "company-dna",
    "/api/v1/dashboard/jd-insights": "jd-insights",
    "/api/v1/expert-panel/ask": "expert-panel",
}


def _today_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _extract_user_id_from_request(request: Request) -> str | None:
    """Authorization 헤더의 Bearer JWT에서 user_id(sub 클레임)를 추출한다.
    실패 시 None 반환 — 기존 동작 유지."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header[len("Bearer "):]
    try:
        import jwt
        from app.config import settings
        secret = settings.SUPABASE_JWT_SECRET
        if not secret:
            # JWT_SECRET 미설정 시 서명 검증 없이 페이로드만 파싱 (개발 환경 허용)
            payload = jwt.decode(token, options={"verify_signature": False})
        else:
            payload = jwt.decode(
                token,
                secret,
                algorithms=["HS256"],
                options={"verify_aud": False},
            )
        return payload.get("sub")
    except Exception:
        return None


def record_api_call(user_id: str, path: str) -> None:
    """인메모리 버퍼에 API 호출 기록 (스레드 안전)"""
    today = _today_str()
    with _buffer_lock:
        buf = _usage_buffer[user_id]

        # 일별 호출 수 증가
        buf["daily_api_calls"][today] = buf["daily_api_calls"].get(today, 0) + 1

        # 뷰 접근 경로인 경우 view_access 카운터 증가
        view_name = _VIEW_PATH_MAP.get(path)
        if view_name:
            buf["view_access"][view_name] = buf["view_access"].get(view_name, 0) + 1


def get_buffered_stats(user_id: str) -> dict:
    """특정 사용자의 인메모리 버퍼 통계 반환"""
    with _buffer_lock:
        buf = _usage_buffer.get(user_id)
        if buf is None:
            return {"daily_api_calls": {}, "view_access": {}, "expert_panel_calls": {}}
        return dict(buf)


def get_expert_panel_daily_count(user_id: str) -> int:
    """Expert Panel /ask 경로의 오늘 호출 횟수를 반환"""
    with _buffer_lock:
        buf = _usage_buffer.get(user_id, {})
        today = _today_str()
        return buf.get("expert_panel_calls", {}).get(today, 0)


def record_expert_panel_call(user_id: str) -> None:
    """Expert Panel /ask 호출을 별도 카운터로 기록 (스레드 안전)"""
    today = _today_str()
    with _buffer_lock:
        buf = _usage_buffer[user_id]
        if "expert_panel_calls" not in buf:
            buf["expert_panel_calls"] = {}
        buf["expert_panel_calls"][today] = buf["expert_panel_calls"].get(today, 0) + 1


def flush_to_db(user_id: str) -> None:
    """인메모리 버퍼를 DB의 usage_stats에 머지하여 저장 (동기, 스레드 안전)"""
    import uuid as _uuid
    from app.database import SessionLocal

    # 버퍼 스냅샷 추출 후 즉시 초기화 (락 범위 최소화)
    with _buffer_lock:
        buf = _usage_buffer.get(user_id)
        if not buf:
            return
        # 스냅샷 복사 후 버퍼 초기화
        buf_snapshot = {
            "daily_api_calls": dict(buf.get("daily_api_calls", {})),
            "view_access": dict(buf.get("view_access", {})),
            "expert_panel_calls": dict(buf.get("expert_panel_calls", {})),
        }
        _usage_buffer[user_id] = {
            "daily_api_calls": {},
            "view_access": {},
            "expert_panel_calls": {},
        }

    if SessionLocal is None:
        logger.warning("usage_stats flush 건너뜀 — DB 미연결")
        return

    db = SessionLocal()
    try:
        from app.models.user import UserProfile
        try:
            uid = _uuid.UUID(user_id)
        except ValueError:
            return

        profile = db.query(UserProfile).filter(UserProfile.id == uid).first()
        if not profile:
            return

        # 기존 DB 값과 머지
        existing: dict = profile.usage_stats or {}
        existing_calls: dict = existing.get("daily_api_calls", {})
        existing_views: dict = existing.get("view_access", {})
        existing_expert: dict = existing.get("expert_panel_calls", {})

        # 일별 호출수 머지 (누적 합산)
        for date_str, count in buf_snapshot["daily_api_calls"].items():
            existing_calls[date_str] = existing_calls.get(date_str, 0) + count

        # 뷰 접근수 머지 (누적 합산)
        for view_name, count in buf_snapshot["view_access"].items():
            existing_views[view_name] = existing_views.get(view_name, 0) + count

        # expert_panel_calls 머지 (누적 합산) — 서버 재시작 시 일일 한도 보존
        for date_str, count in buf_snapshot["expert_panel_calls"].items():
            existing_expert[date_str] = existing_expert.get(date_str, 0) + count

        profile.usage_stats = {
            "daily_api_calls": existing_calls,
            "view_access": existing_views,
            "expert_panel_calls": existing_expert,
        }
        db.commit()
    except Exception as e:
        logger.warning(f"usage_stats flush 실패 (user_id={user_id}): {e}")
        db.rollback()
    finally:
        db.close()


class UsageTrackerMiddleware(BaseHTTPMiddleware):
    """인증된 사용자의 API 호출을 인메모리 카운터로 추적하는 미들웨어"""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        # 인증 실패(401/403) 또는 정적 리소스는 추적 제외
        if response.status_code in (401, 403):
            return response
        if request.url.path in ("/health", "/docs", "/redoc", "/openapi.json"):
            return response

        # request.state.user_id 우선 사용, 없으면 JWT에서 직접 추출
        user_id: str | None = getattr(request.state, "user_id", None)
        if not user_id:
            user_id = _extract_user_id_from_request(request)

        if user_id:
            record_api_call(user_id, request.url.path)

        return response
