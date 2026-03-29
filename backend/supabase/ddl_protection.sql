-- =============================================================================
-- DDL Protection: 클라이언트 역할의 스키마 변경 권한 제거
--
-- 목적: Supabase 클라이언트 SDK가 사용하는 `anon`, `authenticated` 역할이
--       Hire-Intelligence 소유 테이블/스키마를 생성·수정·삭제(DDL)하지 못하도록 제한한다.
--       DML(SELECT, INSERT, UPDATE, DELETE)은 정상적으로 허용된다.
--
-- 주의: `postgres`(슈퍼유저)와 `service_role`은 Alembic 마이그레이션을 위해
--       DDL 권한을 유지해야 하므로 이 파일에서 제한하지 않는다.
--
-- ⚠️  이 스크립트는 Hire-Intelligence 소유 스키마/테이블만 대상으로 한다.
--     공유 DB의 다른 서비스에는 영향을 주지 않는다.
--
-- 대상 스키마: pulse, ops (HI 전용 스키마)
-- 대상 테이블: public 스키마 내 HI 소유 테이블만 (명시적 열거)
-- 대상 역할:   anon (익명 사용자), authenticated (인증된 사용자)
-- =============================================================================


-- =============================================================================
-- 섹션 1: pulse 스키마 — DDL 권한 제거 (HI 전용 스키마)
-- 설명: pulse 스키마에 대한 CREATE 권한을 회수한다.
--       pulse 스키마가 없으면 안전하게 건너뛴다.
-- =============================================================================

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = 'pulse') THEN
        EXECUTE 'REVOKE CREATE ON SCHEMA pulse FROM anon';
        EXECUTE 'REVOKE CREATE ON SCHEMA pulse FROM authenticated';
    END IF;
END;
$$;


-- =============================================================================
-- 섹션 2: ops 스키마 — DDL 권한 제거 (HI 전용 스키마)
-- 설명: ops 스키마에 대한 CREATE 권한을 회수한다.
--       ops 스키마가 없으면 안전하게 건너뛴다.
-- =============================================================================

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = 'ops') THEN
        EXECUTE 'REVOKE CREATE ON SCHEMA ops FROM anon';
        EXECUTE 'REVOKE CREATE ON SCHEMA ops FROM authenticated';
    END IF;
END;
$$;


-- =============================================================================
-- 섹션 3: HI 소유 테이블의 TRIGGER/REFERENCES 권한 제거 (public 스키마)
-- 설명: public 스키마 내 Hire-Intelligence 소유 테이블만 대상으로 한다.
--       다른 서비스의 테이블에는 영향을 주지 않는다.
-- =============================================================================

DO $$
DECLARE
    hi_tables text[] := ARRAY['user_profiles', 'organizations', 'organization_members'];
    tbl text;
BEGIN
    FOREACH tbl IN ARRAY hi_tables
    LOOP
        IF EXISTS (SELECT 1 FROM pg_tables WHERE schemaname = 'public' AND tablename = tbl) THEN
            EXECUTE format('REVOKE TRIGGER, REFERENCES ON public.%I FROM anon', tbl);
            EXECUTE format('REVOKE TRIGGER, REFERENCES ON public.%I FROM authenticated', tbl);
        END IF;
    END LOOP;
END;
$$;


-- =============================================================================
-- 섹션 4: HI 소유 테이블의 TRIGGER/REFERENCES 권한 제거 (pulse 스키마)
-- =============================================================================

DO $$
DECLARE
    tbl text;
BEGIN
    FOR tbl IN
        SELECT tablename FROM pg_tables WHERE schemaname = 'pulse'
    LOOP
        EXECUTE format('REVOKE TRIGGER, REFERENCES ON pulse.%I FROM anon', tbl);
        EXECUTE format('REVOKE TRIGGER, REFERENCES ON pulse.%I FROM authenticated', tbl);
    END LOOP;
END;
$$;


-- =============================================================================
-- 섹션 5: HI 소유 테이블의 TRIGGER/REFERENCES 권한 제거 (ops 스키마)
-- =============================================================================

DO $$
DECLARE
    tbl text;
BEGIN
    FOR tbl IN
        SELECT tablename FROM pg_tables WHERE schemaname = 'ops'
    LOOP
        EXECUTE format('REVOKE TRIGGER, REFERENCES ON ops.%I FROM anon', tbl);
        EXECUTE format('REVOKE TRIGGER, REFERENCES ON ops.%I FROM authenticated', tbl);
    END LOOP;
END;
$$;


-- =============================================================================
-- 섹션 6: DML 권한 명시적 보존 확인 (참고용 주석)
-- 설명: 아래 권한들은 RLS 정책(rls.sql)에 의해 행 단위로 제어되며,
--       이 파일에서는 제거하지 않는다. DML은 정상 동작해야 한다.
--
--   GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO anon;
--   GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO authenticated;
--   (pulse, ops 스키마도 동일)
--
-- 위 GRANT는 Supabase 기본 설정에 의해 이미 부여되어 있으며,
-- 이 파일은 해당 DML 권한을 건드리지 않는다.
-- =============================================================================


-- =============================================================================
-- 섹션 7: 향후 생성 테이블에 대한 기본 권한 설정 (pulse, ops 스키마만)
-- 설명: postgres 또는 service_role이 마이그레이션으로 새 테이블을 생성할 때
--       `anon`/`authenticated`에게 DML 권한만 자동 부여되도록 기본값을 설정한다.
--       TRIGGER, REFERENCES는 제외하여 DDL 유사 권한을 차단한다.
--
-- ⚠️  public 스키마의 DEFAULT PRIVILEGES는 변경하지 않는다.
--     다른 서비스가 public에 테이블을 생성할 때 영향을 줄 수 있기 때문이다.
-- =============================================================================

-- pulse 스키마 — postgres 역할
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA pulse
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO anon;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA pulse
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO authenticated;

-- pulse 스키마 — service_role
ALTER DEFAULT PRIVILEGES FOR ROLE service_role IN SCHEMA pulse
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO anon;
ALTER DEFAULT PRIVILEGES FOR ROLE service_role IN SCHEMA pulse
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO authenticated;

-- ops 스키마 — postgres 역할
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA ops
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO anon;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA ops
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO authenticated;

-- ops 스키마 — service_role
ALTER DEFAULT PRIVILEGES FOR ROLE service_role IN SCHEMA ops
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO anon;
ALTER DEFAULT PRIVILEGES FOR ROLE service_role IN SCHEMA ops
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO authenticated;
