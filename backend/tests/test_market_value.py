"""시장가치 API 테스트"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.dependencies import get_current_user


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def authed_client(client):
    async def override():
        return {"id": "test-uuid", "email": "test@test.com", "role": "USER", "plan": "STARTER"}
    app.dependency_overrides[get_current_user] = override
    yield client
    app.dependency_overrides.clear()


class TestMarketValueApi:
    def test_calculate_basic(self, authed_client):
        res = authed_client.post("/api/v1/market-value", json={
            "skills": ["python", "react", "aws"],
            "education": "서울대 컴퓨터공학 학사",
            "yearsOfExperience": 5,
            "currentCompany": "카카오",
            "targetSegment": "backend",
        })
        assert res.status_code == 200
        data = res.json()["data"]
        assert "estimatedValueP25" in data
        assert "estimatedValueP50" in data
        assert "estimatedValueP75" in data
        assert data["estimatedValueP25"] < data["estimatedValueP50"] < data["estimatedValueP75"]
        assert "tdsScore" in data
        assert "tdsGrade" in data
        assert "valueDrivers" in data
        assert "improvementTips" in data

    def test_calculate_minimal(self, authed_client):
        res = authed_client.post("/api/v1/market-value", json={})
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["estimatedValueP25"] >= 3000

    def test_segment_rank_format(self, authed_client):
        res = authed_client.post("/api/v1/market-value", json={"skills": ["python"]})
        assert res.status_code == 200
        data = res.json()["data"]
        assert "%" in data["segmentRank"]

    def test_unauthenticated_returns_401(self, client):
        res = client.post("/api/v1/market-value", json={})
        assert res.status_code == 401
