"""
Sprint 4 Dashboard API 통합 테스트
- Health, Dashboard, Admin, Subscription 엔드포인트 검증
- ApiResponse 형식: {"status": "success", "data": ..., "message": null}
- camelCase JSON 키 확인 (Pydantic alias)
"""
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _make_db_mock_for_dashboard():
    """DashboardService가 사용하는 query chain을 반환하는 mock DB 생성"""
    db = MagicMock()

    # func.max(WeeklySnapshot.week) scalar 호출 → 주차 반환
    db.query.return_value.scalar.return_value = "2026-W10"

    # .filter().first() / .all() 체인
    db.query.return_value.filter.return_value.first.return_value = None
    db.query.return_value.filter.return_value.all.return_value = []
    db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
    db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
    db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []

    # .distinct().order_by().limit().all() 체인
    db.query.return_value.distinct.return_value.order_by.return_value.limit.return_value.all.return_value = []

    # .filter().distinct().all()
    db.query.return_value.filter.return_value.distinct.return_value.all.return_value = []

    # count/scalar chains
    db.query.return_value.filter.return_value.count.return_value = 0
    db.query.return_value.filter.return_value.scalar.return_value = 0
    db.query.return_value.first.return_value = None

    return db


# ---------------------------------------------------------------------------
# 1. Health & 기본
# ---------------------------------------------------------------------------

class TestHealthAndBasic:
    def test_health_check(self, client: TestClient):
        """GET /health → 200, status=ok"""
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"

    def test_unauthenticated_dashboard_returns_401(self, client: TestClient):
        """인증 없이 대시보드 접근 → 401"""
        # dependency_overrides가 없는 순수 client를 사용하므로
        # get_current_user가 실제로 호출되어 401을 반환해야 함.
        # authed_client fixture를 쓰지 않고 client 단독으로 호출
        resp = client.get("/api/v1/dashboard/sd-matrix")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# 2. Dashboard 엔드포인트
# ---------------------------------------------------------------------------

class TestDashboardEndpoints:
    def test_sd_matrix_returns_success(self, authed_client: TestClient):
        """GET /api/v1/dashboard/sd-matrix → 200, ApiResponse 형식"""
        db = _make_db_mock_for_dashboard()
        app.dependency_overrides[get_db] = lambda: db

        with patch("app.services.dashboard_service.DashboardService.get_sd_matrix") as mock_svc:
            mock_svc.return_value = {
                "week": "2026-W10",
                "total_demand": 100,
                "market_sd_ratio": 1.2,
                "segments": [],
            }
            resp = authed_client.get("/api/v1/dashboard/sd-matrix")

        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "success"
        assert "data" in body
        assert body["message"] is None

    def test_top_companies_returns_success(self, authed_client: TestClient):
        """GET /api/v1/dashboard/companies → 200"""
        db = _make_db_mock_for_dashboard()
        app.dependency_overrides[get_db] = lambda: db

        with patch("app.services.dashboard_service.DashboardService.get_company_rankings") as mock_svc, \
             patch("app.services.dashboard_service.DashboardService.get_company_wow_changes") as mock_wow:
            mock_svc.return_value = {"companies": []}
            mock_wow.return_value = {}
            resp = authed_client.get("/api/v1/dashboard/companies")

        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "success"
        assert isinstance(body["data"], list)

    def test_hiring_trends_returns_success(self, pro_client: TestClient):
        """GET /api/v1/dashboard/trends → 200 (PRO 필요)"""
        db = _make_db_mock_for_dashboard()
        app.dependency_overrides[get_db] = lambda: db

        with patch("app.services.dashboard_service.DashboardService.get_trends") as mock_svc:
            mock_svc.return_value = {"data_points": []}
            resp = pro_client.get("/api/v1/dashboard/trends")

        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "success"
        assert isinstance(body["data"], list)

    def test_company_timeline_returns_success(self, pro_client: TestClient):
        """GET /api/v1/dashboard/timeline → 200 (PRO 필요)"""
        db = _make_db_mock_for_dashboard()
        app.dependency_overrides[get_db] = lambda: db

        with patch("app.services.dashboard_service.DashboardService.get_timeline") as mock_svc:
            mock_svc.return_value = {"entries": []}
            resp = pro_client.get("/api/v1/dashboard/timeline")

        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "success"
        assert isinstance(body["data"], list)

    def test_sd_matrix_with_week_param(self, authed_client: TestClient):
        """GET /api/v1/dashboard/sd-matrix?week=2026-W10 → 200"""
        db = _make_db_mock_for_dashboard()
        app.dependency_overrides[get_db] = lambda: db

        with patch("app.services.dashboard_service.DashboardService.get_sd_matrix") as mock_svc:
            mock_svc.return_value = {
                "week": "2026-W10",
                "total_demand": 50,
                "market_sd_ratio": 0.9,
                "segments": [],
            }
            resp = authed_client.get("/api/v1/dashboard/sd-matrix?week=2026-W10")

        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "success"
        # 서비스가 올바른 week 파라미터로 호출되었는지 확인
        mock_svc.assert_called_once_with("2026-W10")


# ---------------------------------------------------------------------------
# 3. Plan Access Control
# ---------------------------------------------------------------------------

class TestPlanAccessControl:
    def test_starter_can_access_sd_matrix(self, authed_client: TestClient):
        """STARTER 사용자 → sd-matrix 접근 허용 (200)"""
        db = _make_db_mock_for_dashboard()
        app.dependency_overrides[get_db] = lambda: db

        with patch("app.services.dashboard_service.DashboardService.get_sd_matrix") as mock_svc:
            mock_svc.return_value = {
                "week": "2026-W10",
                "total_demand": 0,
                "market_sd_ratio": 1.0,
                "segments": [],
            }
            resp = authed_client.get("/api/v1/dashboard/sd-matrix")

        assert resp.status_code == 200

    def test_starter_can_access_top_companies(self, authed_client: TestClient):
        """STARTER 사용자 → top-companies(companies) 접근 허용 (200)"""
        db = _make_db_mock_for_dashboard()
        app.dependency_overrides[get_db] = lambda: db

        with patch("app.services.dashboard_service.DashboardService.get_company_rankings") as mock_svc, \
             patch("app.services.dashboard_service.DashboardService.get_company_wow_changes") as mock_wow:
            mock_svc.return_value = {"companies": []}
            mock_wow.return_value = {}
            resp = authed_client.get("/api/v1/dashboard/companies")

        assert resp.status_code == 200

    def test_starter_cannot_access_timeline(self, authed_client: TestClient):
        """STARTER 사용자 → timeline 접근 거부 (403)"""
        db = _make_db_mock_for_dashboard()
        app.dependency_overrides[get_db] = lambda: db

        resp = authed_client.get("/api/v1/dashboard/timeline")
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# 4. Admin 엔드포인트
# ---------------------------------------------------------------------------

class TestAdminEndpoints:
    def test_admin_data_quality_requires_admin(self, authed_client: TestClient):
        """일반 USER → /admin/data-quality 접근 시 403"""
        db = _make_db_mock_for_dashboard()
        app.dependency_overrides[get_db] = lambda: db

        resp = authed_client.get("/api/v1/admin/data-quality")
        assert resp.status_code == 403

    def test_admin_data_quality_returns_success(self, admin_client: TestClient):
        """SUPER_ADMIN → /admin/data-quality → 200, ApiResponse 형식"""
        db = MagicMock()

        # week_rows: JobPosting.week distinct query
        week_row_mock = MagicMock()
        week_row_mock.week = "2026-W10"

        # .query(JobPosting.week).distinct().order_by().limit().all() → [week_row_mock]
        db.query.return_value.distinct.return_value.order_by.return_value.limit.return_value.all.return_value = [week_row_mock]

        # per-week aggregation scalars: sum(count), count(company_id), count(segment_id)
        db.query.return_value.filter.return_value.scalar.return_value = 0
        db.query.return_value.filter.return_value.distinct.return_value.all.return_value = []

        # func.coalesce / func.count scalars via filter chain
        db.query.return_value.filter.return_value.scalar.return_value = 0

        # current_week segment rows
        db.query.return_value.filter.return_value.distinct.return_value.all.return_value = []

        app.dependency_overrides[get_db] = lambda: db

        resp = admin_client.get("/api/v1/admin/data-quality")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "success"
        assert "data" in body
        assert body["message"] is None

    def test_admin_crawl_status_returns_success(self, admin_client: TestClient):
        """SUPER_ADMIN → /admin/crawl-status → 200, ApiResponse 형식"""
        db = MagicMock()
        # CrawlRun last_run = None → 기본 응답
        db.query.return_value.order_by.return_value.first.return_value = None
        app.dependency_overrides[get_db] = lambda: db

        resp = admin_client.get("/api/v1/admin/crawl-status")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "success"
        data = body["data"]
        # camelCase 키 검증
        assert "lastCrawlAt" in data
        assert "nextScheduled" in data
        assert data["nextScheduled"] == "매주 월요일 03:00 KST"

    def test_admin_users_returns_success(self, admin_client: TestClient, mock_supabase):
        """SUPER_ADMIN → /admin/users → 200"""
        mock_supabase.table.return_value.select.return_value.limit.return_value.order.return_value.execute.return_value.data = []
        resp = admin_client.get("/api/v1/admin/users")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "success"
        assert isinstance(body["data"], list)


# ---------------------------------------------------------------------------
# 5. Subscription 엔드포인트
# ---------------------------------------------------------------------------

class TestSubscriptionEndpoints:
    def test_get_plans_returns_three_plans(self, client: TestClient):
        """GET /api/v1/subscriptions/plans → 200, 3개 플랜 (인증 불필요)"""
        resp = client.get("/api/v1/subscriptions/plans")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "success"
        plans = body["data"]["plans"]
        assert len(plans) == 3
        plan_names = {p["name"] for p in plans}
        assert plan_names == {"STARTER", "PRO", "ENTERPRISE"}

    def test_get_current_subscription(self, authed_client: TestClient):
        """GET /api/v1/subscriptions/current → 200, SubscriptionResponse"""
        db = MagicMock()
        # 구독 레코드 없음 → 기본 STARTER 응답
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        app.dependency_overrides[get_db] = lambda: db

        resp = authed_client.get("/api/v1/subscriptions/current")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "success"
        data = body["data"]
        assert data["plan"] == "STARTER"
        assert data["status"] == "active"
