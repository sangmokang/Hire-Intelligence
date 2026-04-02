"""후보자 프로파일러 엔드포인트 테스트"""
import pytest
from fastapi.testclient import TestClient
from app.main import app


# ---------------------------------------------------------------------------
# 401 — 미인증
# ---------------------------------------------------------------------------

def test_candidate_profiler_no_auth(client: TestClient):
    """인증 토큰 없으면 401 반환"""
    resp = client.post(
        "/api/v1/candidate-profiler",
        json={"skills": ["Python", "ML"]},
    )
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# 400 — 빈 바디
# ---------------------------------------------------------------------------

def test_candidate_profiler_empty_body(authed_client: TestClient):
    """입력 정보 없으면 400 반환"""
    resp = authed_client.post("/api/v1/candidate-profiler", json={})
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# 200 — skills 입력
# ---------------------------------------------------------------------------

def test_candidate_profiler_with_skills(authed_client: TestClient):
    """skills만 입력해도 tdsScore 반환"""
    resp = authed_client.post(
        "/api/v1/candidate-profiler",
        json={"skills": ["Python", "ML"]},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    data = body["data"]
    assert "tdsScore" in data
    assert 0 <= data["tdsScore"] <= 100


# ---------------------------------------------------------------------------
# 200 — currentCompany + yearsOfExperience 입력
# ---------------------------------------------------------------------------

def test_candidate_profiler_structured_input(authed_client: TestClient):
    """currentCompany + yearsOfExperience 입력 → 응답 구조 검증"""
    resp = authed_client.post(
        "/api/v1/candidate-profiler",
        json={"currentCompany": "카카오", "yearsOfExperience": 5},
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    # 필수 필드 존재 확인
    assert "tdsScore" in data
    assert "tdsGrade" in data
    assert "applicationDirection" in data
    assert "salaryNegotiation" in data
    assert "competingOffers" in data
    assert "summary" in data
    # 값 범위 검증
    assert 0 <= data["tdsScore"] <= 100
    assert data["tdsGrade"] in ("S", "A", "B", "C", "D")
    # tier1 회사 입력 시 높은 점수 기대 (>= 55)
    assert data["tdsScore"] >= 55


# ---------------------------------------------------------------------------
# 응답 구조 상세 검증
# ---------------------------------------------------------------------------

def test_candidate_profiler_response_structure(authed_client: TestClient):
    """응답 내 applicationDirection, salaryNegotiation 구조 검증"""
    resp = authed_client.post(
        "/api/v1/candidate-profiler",
        json={
            "skills": ["Python", "React", "AWS"],
            "education": "서울대 컴퓨터공학",
            "yearsOfExperience": 3,
        },
    )
    assert resp.status_code == 200
    data = resp.json()["data"]

    direction = data["applicationDirection"]
    assert "type" in direction
    assert direction["type"] in ("UPWARD", "LATERAL", "DOWNWARD")
    assert "candidateTds" in direction

    salary = data["salaryNegotiation"]
    assert "marketP25" in salary
    assert "marketP50" in salary
    assert "marketP75" in salary
    assert "recommendedLeverage" in salary
    assert salary["recommendedLeverage"] in ("HIGH", "MEDIUM", "LOW")

    offers = data["competingOffers"]
    assert isinstance(offers, list)
    assert len(offers) > 0
    offer = offers[0]
    assert "companyName" in offer
    assert "tdsScore" in offer
    assert "likelihood" in offer
