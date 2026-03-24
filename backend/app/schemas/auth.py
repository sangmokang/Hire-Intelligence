from pydantic import EmailStr, Field

from app.schemas.common import CamelModel


class SignUpRequest(CamelModel):
    """회원가입 요청"""
    email: EmailStr
    password: str = Field(min_length=8)
    name: str | None = None
    category: str | None = None  # JOB_SEEKER / INHOUSE_HR / HEADHUNTER / CHRO


class SignInRequest(CamelModel):
    """로그인 요청"""
    email: EmailStr
    password: str


class TokenResponse(CamelModel):
    """토큰 응답"""
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"
    expires_in: int | None = None


class AuthResponse(CamelModel):
    """인증 응답 (토큰 + 사용자 정보)"""
    access_token: str
    refresh_token: str | None = None
    user: dict  # Supabase User 객체


class RefreshRequest(CamelModel):
    """토큰 갱신 요청"""
    refresh_token: str | None = None
