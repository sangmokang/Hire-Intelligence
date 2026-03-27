"""RFC 7807 에러 포맷 테스트"""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_404_returns_json():
    """존재하지 않는 경로 → JSON 응답"""
    response = client.get("/nonexistent-path-xyz")
    assert response.status_code == 404
    data = response.json()
    # FastAPI 기본 404: {"detail": "Not Found"}
    assert "detail" in data


def test_validation_error_format():
    """잘못된 body로 POST → 422 RFC 7807 포맷"""
    response = client.post(
        "/api/v1/auth/login",
        json={"bad_field": "value"},
    )
    assert response.status_code == 422
    data = response.json()
    # RFC 7807 필드 확인
    assert "title" in data
    assert "status" in data
