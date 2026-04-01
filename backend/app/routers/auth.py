from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client

from app.dependencies import get_supabase_client, get_supabase_anon_client, get_current_user
from app.schemas.auth import SignUpRequest, SignInRequest, AuthResponse, RefreshRequest
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=ApiResponse[AuthResponse])
async def signup(
    body: SignUpRequest,
    supabase: Client = Depends(get_supabase_anon_client),
):
    """이메일/패스워드 회원가입"""
    try:
        response = supabase.auth.sign_up(
            {"email": body.email, "password": body.password}
        )
        if response.user is None:
            raise HTTPException(status_code=400, detail="회원가입에 실패했습니다.")

        return ApiResponse(
            data=AuthResponse(
                accessToken=response.session.access_token if response.session else "",
                refreshToken=response.session.refresh_token if response.session else None,
                user={"id": str(response.user.id), "email": response.user.email},
            ),
            message="회원가입이 완료되었습니다.",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=ApiResponse[AuthResponse])
async def login(
    body: SignInRequest,
    supabase: Client = Depends(get_supabase_anon_client),
):
    """이메일/패스워드 로그인"""
    try:
        response = supabase.auth.sign_in_with_password(
            {"email": body.email, "password": body.password}
        )
        if response.user is None or response.session is None:
            raise HTTPException(status_code=401, detail="이메일 또는 패스워드가 올바르지 않습니다.")

        return ApiResponse(
            data=AuthResponse(
                accessToken=response.session.access_token,
                refreshToken=response.session.refresh_token,
                user={"id": str(response.user.id), "email": response.user.email},
            ),
            message="로그인 성공",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail="로그인에 실패했습니다.")


@router.post("/logout", response_model=ApiResponse[None])
async def logout(
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_anon_client),
):
    """로그아웃 (세션 무효화)"""
    try:
        supabase.auth.sign_out()
        return ApiResponse(message="로그아웃 되었습니다.")
    except Exception:
        return ApiResponse(message="로그아웃 되었습니다.")


@router.post("/refresh", response_model=ApiResponse[AuthResponse])
async def refresh_token(
    body: RefreshRequest | None = None,
    supabase: Client = Depends(get_supabase_anon_client),
):
    """액세스 토큰 갱신"""
    try:
        refresh_tok = body.refresh_token if body else None
        response = supabase.auth.refresh_session(refresh_tok)
        if response.session is None:
            raise HTTPException(status_code=401, detail="유효하지 않은 리프레시 토큰입니다.")

        return ApiResponse(
            data=AuthResponse(
                accessToken=response.session.access_token,
                refreshToken=response.session.refresh_token,
                user={"id": str(response.user.id), "email": response.user.email} if response.user else {},
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail="토큰 갱신에 실패했습니다.")


@router.get("/me", response_model=ApiResponse[dict])
async def get_me(current_user: dict = Depends(get_current_user)):
    """현재 로그인 사용자 정보 조회"""
    # Safely extract user_metadata if present
    user_obj = current_user.get("user") or {}
    if hasattr(user_obj, "user_metadata"):
        user_metadata = user_obj.user_metadata or {}
    elif isinstance(user_obj, dict):
        user_metadata = user_obj.get("user_metadata") or {}
    else:
        user_metadata = {}

    return ApiResponse(
        data={
            "id": current_user["id"],
            "email": current_user["email"],
            "name": user_metadata.get("name", ""),
            "role": current_user.get("role", "USER"),
            "category": user_metadata.get("category", "JOB_SEEKER"),
            "plan": current_user.get("plan", "STARTER"),
            "track": "BUSINESS",
            "status": "ACTIVE",
            "authProvider": "EMAIL",
        }
    )
