from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from functools import lru_cache
from supabase import create_client, Client
from app.config import settings

security = HTTPBearer(auto_error=False)


@lru_cache()
def get_supabase_client() -> Client:
    """Supabase 서비스 롤 클라이언트 (싱글톤)"""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)


@lru_cache()
def get_supabase_anon_client() -> Client:
    """Supabase 익명 클라이언트 (싱글톤)"""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    supabase: Client = Depends(get_supabase_client),
) -> dict:
    """현재 로그인 사용자 정보 조회 (JWT 토큰 검증)"""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증 토큰이 필요합니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    try:
        # Supabase를 통해 토큰 유효성 검증
        response = supabase.auth.get_user(token)
        if response.user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="유효하지 않거나 만료된 토큰입니다.",
            )
        return {"id": response.user.id, "email": response.user.email, "user": response.user}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="토큰 검증에 실패했습니다.",
        )


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    supabase: Client = Depends(get_supabase_client),
) -> dict | None:
    """선택적 인증 - 토큰이 없어도 None 반환"""
    if credentials is None:
        return None
    try:
        response = supabase.auth.get_user(credentials.credentials)
        if response.user:
            return {"id": response.user.id, "email": response.user.email, "user": response.user}
        return None
    except Exception:
        return None
