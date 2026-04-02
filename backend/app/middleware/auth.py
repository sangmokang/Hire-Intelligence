from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import re

# 인증 불필요 경로 패턴
PUBLIC_PATHS = [
    r"^/health$",
    r"^/docs",
    r"^/redoc",
    r"^/openapi\.json$",
    r"^/api/v1/auth/signup$",
    r"^/api/v1/auth/login$",
    r"^/api/v1/auth/refresh$",
    # Toss 웹훅 — 서버 간 통신, Bearer 토큰 없음
    r"^/api/v1/payments/webhook$",
]


class AuthMiddleware(BaseHTTPMiddleware):
    """JWT 인증 미들웨어 (선택적 사용 - 현재는 라우터 레벨 의존성 주입 방식 사용)"""

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # 공개 경로는 통과
        for pattern in PUBLIC_PATHS:
            if re.match(pattern, path):
                return await call_next(request)

        # Authorization 헤더 확인
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            # 미들웨어 레벨에서는 강제하지 않음 (라우터에서 처리)
            return await call_next(request)

        return await call_next(request)
