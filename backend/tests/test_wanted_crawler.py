"""원티드 크롤러 테스트 — HTTP 모킹"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.crawler.wanted_crawler import WantedCrawler, WANTED_SEGMENTS


class TestWantedCrawler:
    def test_platform_name(self):
        crawler = WantedCrawler()
        assert crawler.platform_name == "wanted"

    def test_all_segments_defined(self):
        """14개 세그먼트 모두 정의 확인"""
        expected = [
            "dev_server", "dev_frontend", "dev_devops", "dev_mlai",
            "dev_java", "dev_cto", "dev_total", "design",
            "pm_po", "marketing", "hr", "cfo_finance", "sales", "strategy",
        ]
        for seg in expected:
            assert seg in WANTED_SEGMENTS, f"세그먼트 미정의: {seg}"

    @pytest.mark.asyncio
    async def test_fetch_listings_success(self):
        """목록 수집 성공 케이스"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "data": [
                {
                    "id": 12345,
                    "position": "시니어 백엔드 개발자",
                    "company": {"name": "토스"},
                },
                {
                    "id": 12346,
                    "position": "주니어 프론트엔드",
                    "company": {"name": "카카오"},
                },
            ]
        }

        crawler = WantedCrawler()
        with patch("app.services.crawler.wanted_crawler.get_http_client") as mock_client_fn:
            mock_async_client = AsyncMock()
            mock_async_client.get = AsyncMock(return_value=mock_response)
            mock_async_client.__aenter__ = AsyncMock(return_value=mock_async_client)
            mock_async_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_fn.return_value = mock_async_client

            listings = await crawler.fetch_listings("dev_server")

        assert len(listings) == 2
        assert listings[0]["title"] == "시니어 백엔드 개발자"
        assert listings[0]["company_name"] == "토스"
        assert listings[0]["segment_id"] == "dev_server"

    @pytest.mark.asyncio
    async def test_fetch_listings_unknown_segment(self):
        """미지원 세그먼트 → 빈 목록"""
        crawler = WantedCrawler()
        listings = await crawler.fetch_listings("unknown_segment")
        assert listings == []

    @pytest.mark.asyncio
    async def test_fetch_detail_success(self):
        """상세 조회 성공"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "job": {
                "position": "백엔드 개발자",
                "intro": "토스 서버팀에서...",
                "main_tasks": "API 설계 및 개발",
                "requirements": "Java 5년 이상",
                "preferred": "Kafka 경험",
                "benefits": "자유로운 근무 환경",
                "salary": {"min": 5000, "max": 8000},
            }
        }

        crawler = WantedCrawler()
        listing = {
            "external_id": "12345",
            "title": "백엔드 개발자",
            "company_name": "토스",
            "url": "https://www.wanted.co.kr/wd/12345",
            "segment_id": "dev_server",
        }

        with patch("app.services.crawler.wanted_crawler.get_http_client") as mock_client_fn:
            mock_async_client = AsyncMock()
            mock_async_client.get = AsyncMock(return_value=mock_response)
            mock_async_client.__aenter__ = AsyncMock(return_value=mock_async_client)
            mock_async_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_fn.return_value = mock_async_client

            detail = await crawler.fetch_detail(listing)

        assert detail is not None
        assert "API 설계 및 개발" in detail["raw_text"]
        assert detail["salary_min"] == 5000
        assert detail["salary_max"] == 8000
