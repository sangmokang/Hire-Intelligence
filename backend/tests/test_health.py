"""헬스체크 + 메타데이터 엔드포인트 테스트"""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app, raise_server_exceptions=False)


def test_health_returns_200():
    """GET /health → 200"""
    response = client.get("/health")
    assert response.status_code == 200


def test_health_returns_ok_status():
    """GET /health → { status: 'ok' }"""
    response = client.get("/health")
    data = response.json()
    assert data["status"] == "ok"
    assert "app" in data
    assert "version" in data


def test_metadata_endpoint_exists():
    """GET /api/v1/dashboard/metadata 엔드포인트 존재 (인증 불필요)"""
    response = client.get("/api/v1/dashboard/metadata")
    # DB 없이도 200 또는 500 허용 — 404가 아니면 라우트 등록 확인
    assert response.status_code != 404
