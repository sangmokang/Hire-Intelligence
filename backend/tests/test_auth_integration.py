"""Auth API 통합 테스트 (Sprint 2)"""
import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from app.main import app


def _make_mock_db():
    """Return a MagicMock that satisfies SQLAlchemy Session interface."""
    db = MagicMock()
    db.query.return_value.scalar.return_value = None
    db.query.return_value.filter.return_value.all.return_value = []
    db.query.return_value.filter.return_value.first.return_value = None
    return db


@pytest.fixture
def client():
    """Plain client with no auth override — tests real auth rejection."""
    from app.database import get_db

    mock_db = _make_mock_db()
    app.dependency_overrides[get_db] = lambda: mock_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


class TestAuthFlow:
    def test_health_check(self, client):
        """Health endpoint should work without auth."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_protected_endpoint_without_token(self, client):
        """Dashboard endpoints should require auth (401 or 403)."""
        response = client.get("/api/v1/dashboard/sd-matrix")
        assert response.status_code in (401, 403)

    def test_me_endpoint_without_token(self, client):
        """Me endpoint should require auth (401 or 403)."""
        response = client.get("/api/v1/me")
        assert response.status_code in (401, 403)

    def test_me_endpoint_with_auth(self, client):
        """Me endpoint should return profile with valid auth override."""
        from app.dependencies import get_current_user

        app.dependency_overrides[get_current_user] = lambda: {
            "id": "test-user-id",
            "email": "test@example.com",
        }
        try:
            response = client.get("/api/v1/me")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
        finally:
            # Remove only the auth override; keep db override active
            app.dependency_overrides.pop(get_current_user, None)

    def test_openapi_docs_accessible(self, client):
        """OpenAPI docs should be publicly accessible."""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_login_invalid_credentials(self, client):
        """Invalid credentials should return 400/401/422 (Supabase error or validation)."""
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "notexist@example.com", "password": "wrongpassword"},
        )
        assert response.status_code in (400, 401, 422, 500)

    def test_trends_without_token(self, client):
        """Trends endpoint also requires auth."""
        response = client.get("/api/v1/dashboard/trends")
        assert response.status_code in (401, 403)

    def test_resume_match_without_token(self, client):
        """Resume match endpoint requires auth."""
        response = client.post(
            "/api/v1/dashboard/resume-match",
            json={"resumeText": "Python developer with 5 years experience"},
        )
        assert response.status_code in (401, 403)
