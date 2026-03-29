-- user_profiles 자동 생성 트리거
-- auth.users에 신규 사용자가 INSERT될 때 public.user_profiles 행을 자동으로 생성한다.
-- 멱등성(idempotent) 보장: 함수/트리거가 이미 존재하면 교체한다.

CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    INSERT INTO public.user_profiles (
        id,
        role,
        category,
        created_at,
        updated_at
    )
    VALUES (
        NEW.id,
        'USER',   -- 기본 역할
        NULL,     -- 카테고리 미분류
        NOW(),
        NOW()
    )
    ON CONFLICT (id) DO NOTHING;  -- 중복 실행 시 무시 (idempotent)

    RETURN NEW;
END;
$$;

-- 기존 트리거가 있으면 삭제 후 재생성 (idempotent)
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;

CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_new_user();
