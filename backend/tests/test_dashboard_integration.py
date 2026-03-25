"""Dashboard API 통합 테스트 (Sprint 2)"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient
from app.main import app

# Mock authenticated user
MOCK_USER = {"id": "test-user-id", "email": "test@example.com"}


def _make_mock_db():
    """Return a MagicMock that satisfies SQLAlchemy Session interface."""
    db = MagicMock()
    # query(...).scalar() -> None  (no latest week)
    db.query.return_value.scalar.return_value = None
    db.query.return_value.filter.return_value.all.return_value = []
    db.query.return_value.filter.return_value.scalar.return_value = None
    db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
    db.query.return_value.filter.return_value.filter.return_value.all.return_value = []
    db.query.return_value.filter.return_value.first.return_value = None
    db.query.return_value.order_by.return_value.limit.return_value.all.return_value = []
    db.query.return_value.join.return_value.filter.return_value.all.return_value = []
    db.query.return_value.join.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
    return db


@pytest.fixture
def client():
    """Override auth + DB dependencies to isolate from external services."""
    from app.dependencies import get_current_user
    from app.database import get_db

    mock_db = _make_mock_db()

    app.dependency_overrides[get_current_user] = lambda: MOCK_USER
    app.dependency_overrides[get_db] = lambda: mock_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


class TestSDMatrix:
    def test_get_sd_matrix_success(self, client):
        response = client.get("/api/v1/dashboard/sd-matrix")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "data" in data
        # data.data should have summary and segments
        assert "summary" in data["data"]
        assert "segments" in data["data"]

    def test_get_sd_matrix_with_week(self, client):
        response = client.get("/api/v1/dashboard/sd-matrix?week=2026-W10")
        assert response.status_code == 200

    def test_get_sd_matrix_empty_db_returns_valid_shape(self, client):
        """Empty DB should return success with empty segments, not 500."""
        response = client.get("/api/v1/dashboard/sd-matrix")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["data"]["segments"], list)


class TestCompanies:
    def test_get_top_companies(self, client):
        response = client.get("/api/v1/dashboard/companies")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert isinstance(data["data"], list)

    def test_get_top_companies_with_filter(self, client):
        response = client.get("/api/v1/dashboard/companies?segment_id=backend&limit=5")
        assert response.status_code == 200

    def test_get_top_companies_limit_validation(self, client):
        """limit=0 should fail validation."""
        response = client.get("/api/v1/dashboard/companies?limit=0")
        assert response.status_code == 422

    def test_get_top_companies_limit_max(self, client):
        """limit=51 should fail validation."""
        response = client.get("/api/v1/dashboard/companies?limit=51")
        assert response.status_code == 422


class TestTimeline:
    def test_get_timeline(self, client):
        response = client.get("/api/v1/dashboard/timeline")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert isinstance(data["data"], list)

    def test_get_timeline_with_company_filter(self, client):
        response = client.get("/api/v1/dashboard/timeline?company_id=some-company-id")
        assert response.status_code == 200


class TestTrends:
    def test_get_trends(self, client):
        response = client.get("/api/v1/dashboard/trends")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert isinstance(data["data"], list)

    def test_get_trends_with_segment(self, client):
        response = client.get("/api/v1/dashboard/trends?segment_id=frontend")
        assert response.status_code == 200


class TestResumeMatch:
    def test_resume_match(self, client):
        response = client.post("/api/v1/dashboard/resume-match", json={
            "resumeText": "Python, React 개발자 경력 5년",
            "maxResults": 5,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "data" in data
        assert "matches" in data["data"]
        assert "extractedKeywords" in data["data"]

    def test_resume_match_missing_body(self, client):
        """Missing resumeText should return 422."""
        response = client.post("/api/v1/dashboard/resume-match", json={})
        assert response.status_code == 422

    def test_resume_match_too_short_text(self, client):
        """resumeText shorter than min_length=10 should return 422."""
        response = client.post("/api/v1/dashboard/resume-match", json={
            "resumeText": "짧음",
        })
        assert response.status_code == 422


class TestCompanyAnalysis:
    def test_company_analysis_not_found(self, client):
        """Non-existent company_id should return 404."""
        response = client.get(
            "/api/v1/dashboard/company-analysis/00000000-0000-0000-0000-000000000000"
        )
        assert response.status_code == 404

    def test_company_analysis_invalid_id_format(self, client):
        """Any string company_id that does not exist returns 404."""
        response = client.get("/api/v1/dashboard/company-analysis/nonexistent-id")
        assert response.status_code == 404
