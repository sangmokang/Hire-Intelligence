"""TDS 시뮬레이터 API 테스트"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.tds_calculator import _calculate_tds, _tds_grade, _tds_percentile

client = TestClient(app)


# TDS 공식 정확성 테스트
class TestTdsCalculator:
    def test_calculate_tds_formula(self):
        """EDS×0.45 + CDS×0.35 + PDS×0.20 공식 검증"""
        result = _calculate_tds(80.0, 70.0, 60.0)
        expected = round(80.0 * 0.45 + 70.0 * 0.35 + 60.0 * 0.20, 1)
        assert result == expected

    def test_tds_grade_s(self):
        assert _tds_grade(90.0) == "S"

    def test_tds_grade_a(self):
        assert _tds_grade(75.0) == "A"

    def test_tds_grade_b(self):
        assert _tds_grade(60.0) == "B"

    def test_tds_grade_c(self):
        assert _tds_grade(45.0) == "C"

    def test_tds_grade_d(self):
        assert _tds_grade(35.0) == "D"

    def test_tds_percentile(self):
        assert _tds_percentile(80.0) == 20.0
        assert _tds_percentile(50.0) == 50.0


# API 엔드포인트 테스트
class TestTdsSimulatorApi:
    def test_simulate_basic(self, client, mock_user):
        res = client.post("/api/v1/tds-simulator", json={
            "education": "서울대 컴퓨터공학 학사",
            "currentCompany": "카카오",
            "yearsOfExperience": 5,
            "skills": ["python", "fastapi", "aws"],
            "targetSegment": "backend",
        })
        assert res.status_code == 200
        data = res.json()["data"]
        assert "tdsScore" in data
        assert "grade" in data
        assert "percentile" in data
        assert "benchmarkComparison" in data
        assert len(data["recommendations"]) == 3

    def test_simulate_minimal_input(self, client, mock_user):
        res = client.post("/api/v1/tds-simulator", json={})
        assert res.status_code == 200

    def test_simulate_grade_in_response(self, client, mock_user):
        res = client.post("/api/v1/tds-simulator", json={
            "education": "박사",
            "currentCompany": "카카오",
            "yearsOfExperience": 10,
            "skills": ["python", "ml", "pytorch", "tensorflow", "aws", "gcp"],
        })
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["grade"] in ("S", "A", "B", "C", "D")
