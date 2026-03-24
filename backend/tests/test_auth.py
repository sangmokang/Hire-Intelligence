from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    """서버 헬스체크 테스트"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "app" in data
    assert "version" in data


def test_login_invalid_credentials():
    """잘못된 자격증명으로 로그인 시도"""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "notexist@example.com", "password": "wrongpassword"},
    )
    # Supabase 오류 또는 401 반환 예상
    assert response.status_code in (400, 401, 422)


def test_protected_endpoint_without_token():
    """인증 없이 보호된 엔드포인트 접근"""
    response = client.get("/api/v1/dashboard/sd-matrix")
    assert response.status_code == 403  # HTTPBearer auto_error=False -> 401


def test_openapi_docs():
    """OpenAPI 문서 접근 가능 여부"""
    response = client.get("/docs")
    assert response.status_code == 200
