"""사람인 HTML 크롤러 (Stretch Goal)"""
import logging
from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup

from app.services.crawler.base import (
    BaseCrawler, polite_delay, get_http_client,
)

logger = logging.getLogger(__name__)

SARAMIN_SEARCH_URL = "https://www.saramin.co.kr/zf_user/search/recruit"

# 사람인 세그먼트별 검색 키워드 (scraper.mjs 기반)
SARAMIN_KEYWORDS: dict[str, list[str]] = {
    "dev_server":   ["서버엔지니어", "백엔드 개발자"],
    "dev_frontend": ["프론트엔드 개발자", "프론트엔드 엔지니어"],
    "dev_devops":   ["DevOps 엔지니어", "인프라 엔지니어"],
    "dev_mlai":     ["머신러닝 엔지니어", "AI 개발자"],
    "dev_java":     ["자바 개발자", "Java 개발자"],
    "dev_cto":      ["CTO", "기술이사"],
    "dev_total":    ["소프트웨어 개발자", "SW 엔지니어"],
    "design":       ["UX 디자이너", "UI 디자이너"],
    "pm_po":        ["프로덕트 매니저", "PM"],
    "marketing":    ["마케터", "디지털 마케팅"],
    "hr":           ["인사담당자", "HR 매니저"],
    "cfo_finance":  ["재무담당자", "CFO"],
    "sales":        ["영업담당자", "세일즈"],
    # strategy 제외 (13 segments)
}


class SaraminCrawler(BaseCrawler):
    """사람인 HTML 스크래핑 기반 크롤러"""

    @property
    def platform_name(self) -> str:
        return "saramin"

    async def fetch_listings(self, segment_id: str) -> list[dict]:
        """세그먼트별 사람인 채용공고 목록 수집"""
        keywords = SARAMIN_KEYWORDS.get(segment_id)
        if not keywords:
            logger.warning(f"사람인 세그먼트 미지원: {segment_id}")
            return []

        listings = []
        async with get_http_client() as client:
            for keyword in keywords:
                try:
                    params = {
                        "searchType": "search",
                        "searchword": keyword,
                        "recruitPage": 1,
                        "recruitSort": "relation",
                        "recruitPageCount": 40,
                    }
                    resp = await client.get(SARAMIN_SEARCH_URL, params=params)
                    resp.raise_for_status()
                    html = resp.text

                    soup = BeautifulSoup(html, "lxml")
                    job_items = soup.select(".item_recruit")

                    for item in job_items:
                        title_el = item.select_one(".job_tit a")
                        company_el = item.select_one(".corp_name a")

                        if not title_el or not company_el:
                            continue

                        title = title_el.get_text(strip=True)
                        company_name = company_el.get_text(strip=True)
                        href = title_el.get("href", "")
                        url = f"https://www.saramin.co.kr{href}" if href else ""

                        # rec_idx 쿼리 파라미터 추출, 없으면 경로 마지막 세그먼트로 폴백
                        if href:
                            parsed_href = urlparse(href)
                            qs = parse_qs(parsed_href.query)
                            external_id = (qs.get("rec_idx") or [parsed_href.path.split("/")[-1]])[0]
                        else:
                            external_id = ""

                        listings.append({
                            "external_id": external_id,
                            "title": title,
                            "company_name": company_name,
                            "url": url,
                            "segment_id": segment_id,
                        })

                except Exception as e:
                    logger.error(f"사람인 크롤링 실패 [{segment_id}/{keyword}]: {e}")
                    self.context.total_errors += 1
                    self.context.errors.append({
                        "segment_id": segment_id,
                        "keyword": keyword,
                        "error": str(e),
                        "phase": "fetch_listings",
                    })

                await polite_delay()

        self.context.total_fetched += len(listings)
        logger.info(f"사람인 [{segment_id}] {len(listings)}건 목록 수집 완료")
        return listings

    async def fetch_detail(self, listing: dict) -> dict | None:
        """사람인 공고 상세 페이지에서 JD 전문 수집"""
        url = listing.get("url", "")
        if not url:
            return None

        async with get_http_client() as client:
            try:
                resp = await client.get(url)
                resp.raise_for_status()
                html = resp.text
            except Exception as e:
                logger.error(f"사람인 상세 조회 실패 [{url}]: {e}")
                self.context.total_errors += 1
                return None

        soup = BeautifulSoup(html, "lxml")

        # 상세 내용 영역 추출 (사람인 구조에 맞게)
        detail_el = soup.select_one(".user_content") or soup.select_one(".view_detail")
        raw_text = detail_el.get_text(separator="\n", strip=True) if detail_el else ""

        return {
            **listing,
            "raw_text": raw_text,
            "salary_min": None,
            "salary_max": None,
        }
