"""JD 인사이트 API 테스트"""
import pytest
from unittest.mock import patch, MagicMock


class TestJdInsightsEndpoint:
    """GET /api/v1/dashboard/jd-insights 테스트"""

    @patch("app.routers.dashboard.JdInsightsService")
    def test_jd_insights_success(self, mock_service_cls, client, mock_pro_user):
        """PRO 사용자 — 정상 응답"""
        mock_service = MagicMock()
        mock_service.get_insights.return_value = {
            "tech_trends": [{"name": "Python", "count": 50, "previous_count": 40, "change": 10}],
            "experience_distribution": [{"level": "senior", "count": 30, "percentage": 60.0}],
            "salary_benchmarks": [],
            "top_domain_tags": [{"name": "핀테크", "count": 15}],
            "total_analyzed": 100,
        }
        mock_service_cls.return_value = mock_service

        response = client.get("/api/v1/dashboard/jd-insights")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["totalAnalyzed"] == 100

    @patch("app.routers.dashboard.JdInsightsService")
    def test_jd_insights_with_segment_filter(self, mock_service_cls, client, mock_pro_user):
        """세그먼트 필터 파라미터"""
        mock_service = MagicMock()
        mock_service.get_insights.return_value = {
            "tech_trends": [],
            "experience_distribution": [],
            "salary_benchmarks": [],
            "top_domain_tags": [],
            "total_analyzed": 0,
        }
        mock_service_cls.return_value = mock_service

        response = client.get("/api/v1/dashboard/jd-insights?segment_id=dev_server&weeks=4")
        assert response.status_code == 200
        mock_service.get_insights.assert_called_once_with(
            segment_id="dev_server",
            weeks=4,
        )

    def test_jd_insights_starter_forbidden(self, client, mock_user):
        """STARTER 사용자 → 403"""
        response = client.get("/api/v1/dashboard/jd-insights")
        assert response.status_code == 403
