from fastapi import Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from app.schemas.common import ApiError
import re

# 엔드포인트별 rate limit 설정 (요청수/분)
RATE_LIMITS: dict[str, int] = {
    "default": 100,
    "admin": 30,
    "auth": 20,
}

# 인메모리 요청 카운터 {key: [(timestamp, count)]}
_request_counts: dict[str, list] = defaultdict(list)


def _get_limit_for_path(path: str) -> int:
    """경로에 따른 rate limit 반환"""
    if re.match(r"^/api/v1/admin", path):
        return RATE_LIMITS["admin"]
    if re.match(r"^/api/v1/auth", path):
        return RATE_LIMITS["auth"]
    return RATE_LIMITS["default"]


def _is_rate_limited(key: str, limit: int) -> tuple[bool, int]:
    """요청 카운트 확인 및 rate limit 초과 여부 반환"""
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(minutes=1)

    # 만료된 항목 제거
    _request_counts[key] = [
        ts for ts in _request_counts[key] if ts > window_start
    ]

    count = len(_request_counts[key])
    if count >= limit:
        # 다음 가능 시간 (초)
        oldest = min(_request_counts[key]) if _request_counts[key] else now
        retry_after = int((oldest + timedelta(minutes=1) - now).total_seconds()) + 1
        return True, retry_after

    # 현재 요청 기록
    _request_counts[key].append(now)
    return False, 0


class RateLimitMiddleware(BaseHTTPMiddleware):
    """인메모리 Rate Limiting 미들웨어 (MVP용)"""

    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path

        # 정적 리소스 및 docs 제외
        if path in ("/health", "/docs", "/redoc", "/openapi.json"):
            return await call_next(request)

        # 사용자 식별 (IP 기반, 인증된 경우 user_id 사용)
        client_ip = request.client.host if request.client else "unknown"
        limit = _get_limit_for_path(path)
        rate_key = f"{client_ip}:{path.split('/')[3] if len(path.split('/')) > 3 else 'root'}"

        limited, retry_after = _is_rate_limited(rate_key, limit)
        if limited:
            error = ApiError(
                type="about:blank",
                title="Too Many Requests",
                status=429,
                detail=f"요청 한도를 초과했습니다. {retry_after}초 후 재시도하세요.",
                instance=path,
            )
            return Response(
                content=error.model_dump_json(by_alias=True),
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                media_type="application/json",
                headers={"Retry-After": str(retry_after)},
            )

        return await call_next(request)
