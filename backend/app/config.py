from pydantic_settings import BaseSettings
from typing import Any


class Settings(BaseSettings):
    # App 기본 설정
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

    # CORS 허용 도메인
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # 인증 토큰 만료 시간
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    model_config = {"env_file": ".env", "case_sensitive": True, "extra": "ignore"}


settings = Settings()
