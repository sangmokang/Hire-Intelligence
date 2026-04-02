"""OppAlert 엔드포인트 테스트"""
import pytest
from fastapi.testclient import TestClient


def test_opp_alert_no_auth(client: TestClient):
    """인증 없이 401 반환"""
    resp = client.get("/api/v1/opp-alert")
    assert resp.status_code == 401


def test_opp_alert_ok(authed_client: TestClient, mock_db):
    """인증 있으면 200, 필수 필드 존재"""
    resp = authed_client.get("/api/v1/opp-alert")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    data = body["data"]
    assert "items" in data
    assert "total" in data
    assert "generatedAt" in data
    assert isinstance(data["items"], list)
    assert isinstance(data["total"], int)


def test_opp_alert_limit(authed_client: TestClient, mock_db):
    """limit 파라미터 적용 — items 최대 limit개"""
    resp = authed_client.get("/api/v1/opp-alert?limit=5")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data["items"]) <= 5


def test_opp_alert_item_fields(authed_client: TestClient, mock_db):
    """items 각 항목에 oppScore(0~100), priority(CRITICAL|HIGH|MEDIUM) 검증"""
    resp = authed_client.get("/api/v1/opp-alert")
    assert resp.status_code == 200
    items = resp.json()["data"]["items"]
    valid_priorities = {"CRITICAL", "HIGH", "MEDIUM"}
    for item in items:
        assert 0 <= item["oppScore"] <= 100, f"oppScore out of range: {item['oppScore']}"
        assert item["priority"] in valid_priorities, f"invalid priority: {item['priority']}"
