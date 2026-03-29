"""크롤 트리거 API 테스트"""
import pytest
from unittest.mock import patch, MagicMock

from app.database import get_db
from app.main import app


@pytest.fixture
def mock_db():
    """DB 세션 모킹 — 실제 DB 연결 없이 테스트"""
    db = MagicMock()
    db.add = MagicMock()
    db.commit = MagicMock()
    db.close = MagicMock()

    def override():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override
    yield db
    app.dependency_overrides.pop(get_db, None)


class TestCrawlTriggerEndpoint:
    """POST /api/v1/crawl/trigger 테스트"""

    @patch("app.routers.crawl.check_crawl_running", return_value=False)
    def test_trigger_success(self, mock_check, client, mock_admin, mock_db):
        """관리자 크롤 트리거 성공"""
        response = client.post(
            "/api/v1/crawl/trigger",
            json={"platform": "wanted"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["status"] == "pending"
        # DB에 CrawlRun이 추가됨
        assert mock_db.add.called
        assert mock_db.commit.called

    @patch("app.routers.crawl.check_crawl_running", return_value=True)
    def test_trigger_conflict(self, mock_check, client, mock_admin, mock_db):
        """이미 실행 중인 크롤 → 409"""
        response = client.post(
            "/api/v1/crawl/trigger",
            json={"platform": "wanted"},
        )
        assert response.status_code == 409

    def test_trigger_non_admin(self, client, mock_pro_user):
        """비관리자(PRO) → 403"""
        response = client.post(
            "/api/v1/crawl/trigger",
            json={"platform": "wanted"},
        )
        assert response.status_code == 403

    def test_trigger_invalid_platform(self, client, mock_admin):
        """잘못된 플랫폼 → 422"""
        response = client.post(
            "/api/v1/crawl/trigger",
            json={"platform": "invalid"},
        )
        assert response.status_code == 422


class TestCrawlStatusEndpoint:
    """GET /api/v1/crawl/status/{crawl_run_id} 테스트"""

    @patch("app.routers.crawl.check_crawl_running", return_value=False)
    def test_crawl_status_success(self, mock_check, client, mock_admin, mock_db):
        """크롤 상태 조회 성공 — 올바른 필드 포함"""
        import uuid
        from datetime import datetime, timezone

        # CrawlRun 모킹: trigger 후 생성된 run을 DB 조회가 반환하도록 설정
        crawl_run_id = str(uuid.uuid4())

        mock_run = MagicMock()
        mock_run.id = uuid.UUID(crawl_run_id)
        mock_run.status = "completed"
        mock_run.platform = "wanted"
        mock_run.segment_id = None
        mock_run.total_fetched = 10
        mock_run.total_parsed = 8
        mock_run.total_errors = 2
        mock_run.started_at = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        mock_run.finished_at = datetime(2026, 1, 1, 0, 5, 0, tzinfo=timezone.utc)

        # DB execute chain: scalar_one_or_none() → mock_run
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_run
        mock_db.execute.return_value = mock_result

        response = client.get(f"/api/v1/crawl/status/{crawl_run_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        payload = data["data"]
        assert payload["crawlRunId"] == crawl_run_id
        assert payload["status"] == "completed"
        assert payload["platform"] == "wanted"
        assert payload["totalFetched"] == 10
        assert payload["totalParsed"] == 8
        assert payload["totalErrors"] == 2

    def test_crawl_status_not_found(self, client, mock_admin, mock_db):
        """존재하지 않는 crawl_run_id → 404"""
        import uuid

        missing_id = str(uuid.uuid4())

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        response = client.get(f"/api/v1/crawl/status/{missing_id}")
        assert response.status_code == 404
