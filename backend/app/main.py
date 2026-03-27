import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings

if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        traces_sample_rate=0.1,
        environment=settings.APP_ENV,
    )
from app.routers import auth, dashboard, me, admin
from app.routers.subscription import router as subscription_router
from app.middleware.rate_limit import RateLimitMiddleware
from app.schemas.common import ApiError

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="VXMI 채용 인텔리전스 플랫폼 API",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS 미들웨어
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

# Rate Limiting 미들웨어
app.add_middleware(RateLimitMiddleware)


# RFC 7807 Problem Details 기반 exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """HTTPException → ApiError (RFC 7807)"""
    error = ApiError(
        title=exc.__class__.__name__,
        status=exc.status_code,
        detail=exc.detail,
        instance=str(request.url.path),
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=error.model_dump(by_alias=True),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """RequestValidationError → 422 ApiError (RFC 7807)"""
    # 첫 번째 에러의 메시지를 detail로 사용
    detail = "; ".join(
        f"{' -> '.join(str(loc) for loc in err['loc'])}: {err['msg']}"
        for err in exc.errors()
    )
    error = ApiError(
        type="about:blank",
        title="Unprocessable Entity",
        status=422,
        detail=detail,
        instance=str(request.url.path),
    )
    return JSONResponse(
        status_code=422,
        content=error.model_dump(by_alias=True),
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """예상치 못한 예외 → 500 ApiError (RFC 7807)"""
    error = ApiError(
        type="about:blank",
        title="Internal Server Error",
        status=500,
        detail="서버 내부 오류가 발생했습니다.",
        instance=str(request.url.path),
    )
    return JSONResponse(
        status_code=500,
        content=error.model_dump(by_alias=True),
    )


# 라우터 등록
API_PREFIX = "/api/v1"
app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(dashboard.router, prefix=API_PREFIX)
app.include_router(me.router, prefix=API_PREFIX)
app.include_router(admin.router, prefix=API_PREFIX)
app.include_router(subscription_router, prefix=API_PREFIX)


@app.get("/health", tags=["health"])
async def health_check():
    """서버 상태 확인"""
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }
