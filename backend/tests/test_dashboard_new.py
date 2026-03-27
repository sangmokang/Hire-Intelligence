"""대시보드 플랜 접근 제어 통합 테스트"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.dependencies import get_current_user

client = TestClient(app, raise_server_exceptions=False)


def test_sd_matrix_with_auth_returns_200(mock_user):
    """STARTER 유저 — SD Matrix 접근 가능 (200 or 500 DB 에러 허용)"""
    response = client.get("/api/v1/dashboard/sd-matrix")
    # 인증 통과 → DB 에러는 허용, 403/401은 불가
    assert response.status_code not in (401, 403)


def test_top_companies_with_auth_returns_200(mock_user):
    """STARTER 유저 — Top Companies 접근 가능 (200 or 500 DB 에러 허용)"""
    response = client.get("/api/v1/dashboard/companies")
    assert response.status_code not in (401, 403)


def test_timeline_requires_pro(mock_user):
    """STARTER 유저 — Timeline 접근 불가 → 403"""
    response = client.get("/api/v1/dashboard/timeline")
    assert response.status_code == 403


def test_trends_requires_pro(mock_user):
    """STARTER 유저 — Trends 접근 불가 → 403"""
    response = client.get("/api/v1/dashboard/trends")
    assert response.status_code == 403


def test_resume_match_requires_pro(mock_user):
    """STARTER 유저 — Resume Match 접근 불가 → 403"""
    response = client.post(
        "/api/v1/dashboard/resume-match",
        json={"resume_text": "Python developer", "max_results": 5},
    )
    assert response.status_code == 403


def test_company_analysis_requires_pro(mock_user):
    """STARTER 유저 — Company Analysis 접근 불가 → 403"""
    response = client.get("/api/v1/dashboard/company-analysis/test-company-id")
    assert response.status_code == 403
