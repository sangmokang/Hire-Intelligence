-- =============================================================================
-- DDL Protection: 클라이언트 역할의 스키마 변경 권한 제거
--
-- 목적: Supabase 클라이언트 SDK가 사용하는 `anon`, `authenticated` 역할이
--       테이블/스키마를 생성·수정·삭제(DDL)하지 못하도록 제한한다.
--       DML(SELECT, INSERT, UPDATE, DELETE)은 정상적으로 허용된다.
--
-- 주의: `postgres`(슈퍼유저)와 `service_role`은 Alembic 마이그레이션을 위해
--       DDL 권한을 유지해야 하므로 이 파일에서 제한하지 않는다.
--
-- 대상 스키마: public, pulse, ops
-- 대상 역할:   anon (익명 사용자), authenticated (인증된 사용자)
-- =============================================================================


-- =============================================================================
-- 섹션 1: 데이터베이스 레벨 스키마 생성 권한 제거
-- 설명: `anon`과 `authenticated`가 새로운 스키마 자체를 만들지 못하도록 한다.
-- =============================================================================

REVOKE CREATE ON DATABASE postgres FROM anon;
REVOKE CREATE ON DATABASE postgres FROM authenticated;


-- =============================================================================
-- 섹션 2: public 스키마 — DDL 권한 제거
-- 설명: public 스키마 안에 새 객체(테이블, 함수 등)를 생성하지 못하도록
--       CREATE 권한을 회수한다.
-- =============================================================================

REVOKE CREATE ON SCHEMA public FROM anon;
REVOKE CREATE ON SCHEMA public FROM authenticated;


-- =============================================================================
-- 섹션 3: pulse 스키마 — DDL 권한 제거
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
-- 섹션 4: ops 스키마 — DDL 권한 제거
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
-- 섹션 5: 기존 테이블의 소유권 기반 DDL 방어 (public 스키마)
-- 설명: ALTER TABLE / DROP TABLE은 테이블 소유자 또는 슈퍼유저만 실행할 수 있다.
--       `anon`과 `authenticated`는 테이블 소유자가 아니므로 이미 차단되나,
--       명시적 안전장치로 불필요한 TRIGGER, REFERENCES 권한도 제거한다.
-- =============================================================================

-- public 스키마의 현재 및 미래 테이블에 대해 TRIGGER/REFERENCES 권한 제거
-- (이 권한들은 DDL에 준하는 부작용을 만들 수 있음)
DO $$
DECLARE
    tbl text;
BEGIN
    FOR tbl IN
        SELECT tablename FROM pg_tables WHERE schemaname = 'public'
    LOOP
        EXECUTE format('REVOKE TRIGGER, REFERENCES ON public.%I FROM anon', tbl);
        EXECUTE format('REVOKE TRIGGER, REFERENCES ON public.%I FROM authenticated', tbl);
    END LOOP;
END;
$$;


-- =============================================================================
-- 섹션 6: 기존 테이블의 소유권 기반 DDL 방어 (pulse 스키마)
-- 설명: pulse 스키마 테이블에 동일한 TRIGGER/REFERENCES 권한 제거를 적용한다.
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
-- 섹션 7: 기존 테이블의 소유권 기반 DDL 방어 (ops 스키마)
-- 설명: ops 스키마 테이블에 동일한 TRIGGER/REFERENCES 권한 제거를 적용한다.
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
-- 섹션 8: DML 권한 명시적 보존 확인 (참고용 주석)
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
-- 섹션 9: 향후 생성 테이블에 대한 기본 권한 설정 (DEFAULT PRIVILEGES)
-- 설명: postgres 또는 service_role이 마이그레이션으로 새 테이블을 생성할 때
--       `anon`/`authenticated`에게 DML 권한만 자동 부여되도록 기본값을 설정한다.
--       TRIGGER, REFERENCES는 제외하여 DDL 유사 권한을 차단한다.
-- =============================================================================

-- postgres 역할이 만드는 객체에 대한 기본 권한
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO anon;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO authenticated;

ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA pulse
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO anon;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA pulse
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO authenticated;

ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA ops
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO anon;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA ops
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO authenticated;

-- service_role 역할이 만드는 객체에 대한 기본 권한
-- Alembic이 service_role로 실행될 경우를 대비
ALTER DEFAULT PRIVILEGES FOR ROLE service_role IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO anon;
ALTER DEFAULT PRIVILEGES FOR ROLE service_role IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO authenticated;

ALTER DEFAULT PRIVILEGES FOR ROLE service_role IN SCHEMA pulse
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO anon;
ALTER DEFAULT PRIVILEGES FOR ROLE service_role IN SCHEMA pulse
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO authenticated;

ALTER DEFAULT PRIVILEGES FOR ROLE service_role IN SCHEMA ops
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO anon;
ALTER DEFAULT PRIVILEGES FOR ROLE service_role IN SCHEMA ops
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO authenticated;
