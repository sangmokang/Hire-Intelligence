from supabase import Client
from fastapi import HTTPException, status


class AuthService:
    """Supabase Auth 연동 서비스"""

    def __init__(self, supabase: Client):
        self.supabase = supabase

    def sign_up(self, email: str, password: str) -> dict:
        """회원가입"""
        try:
            response = self.supabase.auth.sign_up({"email": email, "password": password})
            if response.user is None:
                raise HTTPException(status_code=400, detail="회원가입에 실패했습니다.")
            return {"user": response.user, "session": response.session}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    def sign_in(self, email: str, password: str) -> dict:
        """로그인"""
        try:
            response = self.supabase.auth.sign_in_with_password(
                {"email": email, "password": password}
            )
            if response.user is None or response.session is None:
                raise HTTPException(status_code=401, detail="인증에 실패했습니다.")
            return {"user": response.user, "session": response.session}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=401, detail="로그인에 실패했습니다.")

    def get_user(self, token: str) -> dict:
        """토큰으로 사용자 정보 조회"""
        try:
            response = self.supabase.auth.get_user(token)
            if response.user is None:
                raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")
            return {"id": response.user.id, "email": response.user.email}
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=401, detail="토큰 검증에 실패했습니다.")

    def refresh_session(self, refresh_token: str) -> dict:
        """세션 갱신"""
        try:
            response = self.supabase.auth.refresh_session(refresh_token)
            if response.session is None:
                raise HTTPException(status_code=401, detail="세션 갱신에 실패했습니다.")
            return {"session": response.session}
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=401, detail="세션 갱신에 실패했습니다.")
