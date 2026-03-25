# Hire-Intelligence

HR Analytics SaaS — 채용 인텔리전스 대시보드

## Architecture

- **Frontend:** `vxmi-dashboard/` — React 19 + TypeScript (strict) + Vite 8 + Tailwind CSS 4
- **Backend:** `backend/` — FastAPI + SQLAlchemy 2.0 + Alembic
- **Database:** Supabase PostgreSQL
- **Auth:** Supabase Auth (JWT, HttpOnly cookie)

## Commands

```bash
# Frontend
cd vxmi-dashboard && npm run dev      # dev server :5173
cd vxmi-dashboard && npm run build    # tsc + vite build
cd vxmi-dashboard && npm run lint     # eslint
cd vxmi-dashboard && npx playwright test  # e2e tests

# Backend
cd backend && uvicorn app.main:app --reload --port 8000
cd backend && pytest                  # unit + integration tests
cd backend && alembic upgrade head    # run migrations
```

## Conventions

- **API JSON 필드:** 항상 camelCase (Pydantic alias_generator로 변환)
- **Response 형식:** `{ "status": "success", "data": T, "message": null }`
- **Error 형식:** RFC 7807 Problem Details
- **FE 변수/함수:** camelCase, 파일명 camelCase
- **BE 변수/함수:** snake_case, 파일명 snake_case, 클래스 PascalCase
- **한국어 주석:** 비즈니스 로직 설명 시 한국어 주석 사용
- **TypeScript:** strict 모드 필수, 모든 타입 명시

## Key Patterns

- **State:** Zustand (`useXxxStore`) + TanStack Query (서버 상태)
- **API Client:** `src/services/apiClient.ts` — Axios interceptor 기반
- **Mocking:** MSW로 개발 시 API 모킹, Vite proxy로 실제 API 연결
- **DB Models:** UUID PK, `created_at`/`updated_at` with timezone
- **Routing:** FastAPI 도메인별 라우터 분리 (auth, dashboard, me, admin)

## Environment

- Frontend `.env`: `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`, `VITE_API_BASE_URL`
- Backend `.env`: `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET`
- API 계약서: `API_CONTRACT.md` 참조
