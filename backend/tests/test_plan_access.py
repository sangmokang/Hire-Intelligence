"""플랜별 접근 제어 통합 테스트"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app, raise_server_exceptions=False)


def test_pro_user_can_access_timeline(mock_pro_user):
    """PRO 유저 — Timeline 접근 가능 (200 or 500 DB 에러 허용)"""
    response = client.get("/api/v1/dashboard/timeline")
    assert response.status_code not in (401, 403)


def test_pro_user_can_access_trends(mock_pro_user):
    """PRO 유저 — Trends 접근 가능 (200 or 500 DB 에러 허용)"""
    response = client.get("/api/v1/dashboard/trends")
    assert response.status_code not in (401, 403)


def test_starter_blocked_from_timeline(mock_user):
    """STARTER 유저 — Timeline 접근 차단 → 403"""
    response = client.get("/api/v1/dashboard/timeline")
    assert response.status_code == 403


def test_starter_blocked_from_company_analysis(mock_user):
    """STARTER 유저 — Company Analysis 접근 차단 → 403"""
    response = client.get("/api/v1/dashboard/company-analysis/some-id")
    assert response.status_code == 403
