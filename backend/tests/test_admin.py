"""관리자 엔드포인트 통합 테스트"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_admin_users_no_auth():
    """인증 없이 /admin/users → 401 또는 403"""
    response = client.get("/api/v1/admin/users")
    assert response.status_code in (401, 403)


def test_admin_users_regular_user(mock_user):
    """일반 USER 역할 — /admin/users → 403"""
    response = client.get("/api/v1/admin/users")
    assert response.status_code == 403


def test_admin_users_super_admin(mock_admin):
    """SUPER_ADMIN — /admin/users → 200"""
    response = client.get("/api/v1/admin/users")
    assert response.status_code == 200
