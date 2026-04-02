import os
from pydantic_settings import BaseSettings


def _resolve_env_file() -> str:
    """APP_ENV 환경변수에 따라 로드할 .env 파일 결정."""
    app_env = os.getenv("APP_ENV", "development")
    env_file = f".env.{app_env}"
    # 환경별 파일이 없으면 기본 .env로 폴백
    if not os.path.exists(env_file):
        env_file = ".env"
    return env_file


class Settings(BaseSettings):
    # App 기본 설정
    APP_ENV: str = "development"
    APP_NAME: str = "VXMI Hire Intelligence API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    # Supabase 설정
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_JWT_SECRET: str = ""  # JWT 검증용 (선택)

    # 데이터베이스 (Supabase PostgreSQL)
    DATABASE_URL: str = ""

    # CORS 허용 도메인 (와일드카드 금지 — 프로덕션 도메인 명시)
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "https://valuehire.cc",
        "https://www.valuehire.cc",
    ]

    # Sentry 오류 추적
    SENTRY_DSN: str | None = None

    # Slack Incoming Webhook URL (알림 전송용, 미설정 시 알림 비활성화)
    SLACK_WEBHOOK_URL: str | None = None

    # 인증 토큰 만료 시간
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Anthropic API (JD 파싱용)
    ANTHROPIC_API_KEY: str = ""
    JD_PARSER_MODEL: str = "claude-haiku-4-5-20251001"
    JD_PARSER_BATCH_SIZE: int = 10

    # 크롤러 설정
    CRAWL_DELAY_SECONDS: int = 2

    # Resend 이메일 서비스 (Sprint 5 주간 리포트용)
    RESEND_API_KEY: str | None = None
    RESEND_FROM_EMAIL: str = "noreply@hire-intelligence.co.kr"

    # Toss Payments 결제 설정
    TOSS_SECRET_KEY: str = ""
    TOSS_CLIENT_KEY: str = ""
    TOSS_WEBHOOK_SECRET: str = ""

    # 빌링키 암호화 (Fernet 대칭키, cryptography.fernet.Fernet.generate_key()로 생성)
    BILLING_KEY_ENCRYPTION_KEY: str = ""

    model_config = {
        "env_file": _resolve_env_file(),
        "case_sensitive": True,
        "extra": "ignore",
    }


settings = Settings()
