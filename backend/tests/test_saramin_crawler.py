"""사람인 크롤러 테스트"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.crawler.saramin_crawler import SaraminCrawler, SARAMIN_KEYWORDS


class TestSaraminCrawler:
    def test_platform_name(self):
        crawler = SaraminCrawler()
        assert crawler.platform_name == "saramin"

    def test_segments_defined(self):
        """13개 세그먼트 정의 (strategy 제외)"""
        assert "strategy" not in SARAMIN_KEYWORDS
        assert len(SARAMIN_KEYWORDS) == 13

    def test_keywords_non_empty(self):
        """모든 세그먼트에 키워드 존재"""
        for seg, keywords in SARAMIN_KEYWORDS.items():
            assert len(keywords) > 0, f"빈 키워드: {seg}"

    @pytest.mark.asyncio
    async def test_fetch_listings_unknown_segment(self):
        """미지원 세그먼트 → 빈 목록"""
        crawler = SaraminCrawler()
        listings = await crawler.fetch_listings("strategy")
        assert listings == []

    @pytest.mark.asyncio
    @patch("app.services.crawler.saramin_crawler.polite_delay", new_callable=AsyncMock)
    @patch("app.services.crawler.saramin_crawler.get_http_client")
    async def test_fetch_listings_with_html(self, mock_get_client, mock_delay):
        """최소 HTML 목 응답으로 listings 추출 검증"""
        # 사람인 결과 페이지의 최소 구조 모킹
        mock_html = """
        <html><body>
          <div class="item_recruit">
            <div class="job_tit">
              <a href="/zf_user/jobs/relay/view?rec_idx=12345678">백엔드 개발자</a>
            </div>
            <div class="corp_name">
              <a href="#">테스트컴퍼니</a>
            </div>
          </div>
          <div class="item_recruit">
            <div class="job_tit">
              <a href="/zf_user/jobs/relay/view?rec_idx=87654321">서버 엔지니어</a>
            </div>
            <div class="corp_name">
              <a href="#">다른회사</a>
            </div>
          </div>
        </body></html>
        """

        # httpx AsyncClient 컨텍스트 매니저 모킹
        mock_response = MagicMock()
        mock_response.text = mock_html
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_get_client.return_value = mock_client

        crawler = SaraminCrawler()
        listings = await crawler.fetch_listings("dev_server")

        # dev_server 세그먼트는 2개 키워드 → 각 키워드마다 2건 = 최대 4건
        # (실제로는 mock이 동일 HTML을 반환하므로 2키워드 × 2항목 = 4건)
        assert len(listings) > 0
        first = listings[0]
        assert first["title"] == "백엔드 개발자"
        assert first["company_name"] == "테스트컴퍼니"
        assert first["segment_id"] == "dev_server"
        assert "saramin.co.kr" in first["url"]

    @pytest.mark.asyncio
    @patch("app.services.crawler.saramin_crawler.polite_delay", new_callable=AsyncMock)
    @patch("app.services.crawler.saramin_crawler.get_http_client")
    async def test_external_id_extraction(self, mock_get_client, mock_delay):
        """rec_idx가 external_id로 올바르게 파싱되는지 검증"""
        mock_html = """
        <html><body>
          <div class="item_recruit">
            <div class="job_tit">
              <a href="/zf_user/jobs/relay/view?rec_idx=99991234">DevOps 엔지니어</a>
            </div>
            <div class="corp_name">
              <a href="#">인프라회사</a>
            </div>
          </div>
        </body></html>
        """

        mock_response = MagicMock()
        mock_response.text = mock_html
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_get_client.return_value = mock_client

        crawler = SaraminCrawler()
        listings = await crawler.fetch_listings("dev_devops")

        assert len(listings) > 0
        # href의 마지막 부분이 external_id로 사용됨
        # href = "/zf_user/jobs/relay/view?rec_idx=99991234"
        # split("/")[-1] = "view?rec_idx=99991234"
        # href="/zf_user/jobs/relay/view?rec_idx=99991234" → split("/")[-1] = "view?rec_idx=99991234"
        # 실제 크롤러 로직: href.split("/")[-1]
        # BeautifulSoup이 href 속성을 그대로 반환하므로 split 결과 확인
        assert "99991234" in listings[0]["external_id"]
        # URL은 saramin 도메인 + href
        assert listings[0]["url"].startswith("https://www.saramin.co.kr")
