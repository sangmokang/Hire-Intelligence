"""인증 관련 통합 테스트"""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_login_requires_body():
    """POST /api/v1/auth/login — body 없으면 422"""
    response = client.post("/api/v1/auth/login")
    assert response.status_code == 422


def test_protected_endpoint_no_token():
    """인증 토큰 없이 보호된 엔드포인트 접근 → 401 또는 403"""
    response = client.get("/api/v1/me")
    assert response.status_code in (401, 403)


def test_dashboard_sd_matrix_no_auth():
    """SD Matrix — 인증 없이 접근 → 401 또는 403"""
    response = client.get("/api/v1/dashboard/sd-matrix")
    assert response.status_code in (401, 403)


def test_dashboard_top_companies_no_auth():
    """Top Companies — 인증 없이 접근 → 401 또는 403"""
    response = client.get("/api/v1/dashboard/companies")
    assert response.status_code in (401, 403)
