"""
Sprint 4 통합 테스트 — Company DNA + Subscription + Admin API
최소 11개 테스트 (10개 필수 + company-dna 인증 없는 접근 1개)
"""
import pytest


# ---------------------------------------------------------------------------
# Subscription Tests
# ---------------------------------------------------------------------------


def test_get_plans_unauthenticated(client):
    """GET /api/v1/subscriptions/plans — 인증 없이도 200 반환"""
    response = client.get("/api/v1/subscriptions/plans")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"


def test_get_plans_returns_three_plans(client):
    """GET /api/v1/subscriptions/plans — STARTER, PRO, ENTERPRISE 3개 플랜 반환"""
    response = client.get("/api/v1/subscriptions/plans")
    assert response.status_code == 200
    plans = response.json()["data"]["plans"]
    assert len(plans) == 3
    plan_names = {p["name"] for p in plans}
    assert plan_names == {"STARTER", "PRO", "ENTERPRISE"}


def test_get_current_subscription_authenticated(authed_client, mock_db):
    """GET /api/v1/subscriptions/current — 인증된 사용자 200 반환"""
    # mock_db: query().filter().order_by().first() → None (구독 없음, 기본값 반환)
    mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

    response = authed_client.get("/api/v1/subscriptions/current")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["data"] is not None


def test_get_current_subscription_unauthenticated(client):
    """GET /api/v1/subscriptions/current — 인증 없이 401 반환"""
    response = client.get("/api/v1/subscriptions/current")
    assert response.status_code == 401


def test_upgrade_plan_invalid(authed_client, mock_db):
    """POST /api/v1/subscriptions/upgrade — 유효하지 않은 플랜 → 400"""
    response = authed_client.post(
        "/api/v1/subscriptions/upgrade",
        json={"plan": "INVALID"},
    )
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# Admin Tests
# ---------------------------------------------------------------------------


def test_admin_stats_requires_admin(authed_client):
    """GET /api/v1/admin/stats — 일반 USER 접근 시 403"""
    response = authed_client.get("/api/v1/admin/stats")
    assert response.status_code == 403


def test_admin_stats_as_admin(admin_client, mock_supabase):
    """GET /api/v1/admin/stats — SUPER_ADMIN 접근 시 200"""
    mock_supabase.table.return_value.select.return_value.execute.return_value.data = [
        {"status": "ACTIVE", "organization_id": None}
    ]
    response = admin_client.get("/api/v1/admin/stats")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert "totalUsers" in body["data"] or "total_users" in body["data"]


def test_admin_users_as_admin(admin_client, mock_supabase):
    """GET /api/v1/admin/users — SUPER_ADMIN 접근 시 200"""
    mock_supabase.table.return_value.select.return_value.limit.return_value.order.return_value.execute.return_value.data = []
    response = admin_client.get("/api/v1/admin/users")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert isinstance(body["data"], list)


def test_admin_data_quality_as_user_forbidden(authed_client):
    """GET /api/v1/admin/data-quality — 일반 USER 접근 시 403"""
    response = authed_client.get("/api/v1/admin/data-quality")
    assert response.status_code == 403


def test_admin_crawl_status_as_admin(admin_client, mock_db):
    """GET /api/v1/admin/crawl-status — SUPER_ADMIN 접근 시 200, last_run=None 처리"""
    # CrawlRun 없음 → None 반환 → 기본 응답
    mock_db.query.return_value.order_by.return_value.first.return_value = None

    response = admin_client.get("/api/v1/admin/crawl-status")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    data = body["data"]
    assert data["nextScheduled"] == "매주 월요일 03:00 KST"


# ---------------------------------------------------------------------------
# Company DNA Tests
# ---------------------------------------------------------------------------


def test_company_dna_unauthenticated(client):
    """GET /api/v1/dashboard/company-dna/{company_id} — 인증 없이 401"""
    response = client.get("/api/v1/dashboard/company-dna/test-company")
    assert response.status_code == 401
