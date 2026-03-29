"""원티드 API 크롤러"""
import logging
from app.services.crawler.base import (
    BaseCrawler, polite_delay, get_http_client,
    normalize_company_name, is_duplicate_title,
)

logger = logging.getLogger(__name__)

# 원티드 API 세그먼트 매핑 (scraper.mjs 기반)
WANTED_SEGMENTS: dict[str, dict] = {
    "dev_server":   {"job_group_id": 518, "job_ids": 872},
    "dev_frontend": {"job_group_id": 518, "job_ids": 669},
    "dev_devops":   {"job_group_id": 518, "job_ids": 674},
    "dev_mlai":     {"job_group_id": 518, "job_ids": 1634},
    "dev_java":     {"job_group_id": 518, "job_ids": 660},
    "dev_cto":      {"job_group_id": 518, "job_ids": 795},
    "dev_total":    {"job_group_id": 518},
    "design":       {"job_group_id": 511},
    "pm_po":        {"job_group_id": 507, "job_ids": [559, 565]},
    "marketing":    {"job_group_id": 523},
    "hr":           {"job_group_id": 506},
    "cfo_finance":  {"job_group_id": 3006},
    "sales":        {"job_group_id": 524},
    "strategy":     {"job_group_id": 507, "job_ids": 564},
}

WANTED_API_BASE = "https://www.wanted.co.kr/api/v4/jobs"


class WantedCrawler(BaseCrawler):
    """원티드 공개 API 기반 크롤러"""

    @property
    def platform_name(self) -> str:
        return "wanted"

    async def fetch_listings(self, segment_id: str) -> list[dict]:
        """세그먼트별 원티드 채용공고 목록 수집 (페이지네이션 포함)"""
        seg_config = WANTED_SEGMENTS.get(segment_id)
        if not seg_config:
            logger.warning(f"원티드 세그먼트 미지원: {segment_id}")
            return []

        listings = []
        offset = 0
        limit = 20  # 원티드 API 기본 페이지 사이즈

        async with get_http_client() as client:
            while True:
                params: dict = {
                    "country": "kr",
                    "job_sort": "job.latest_order",
                    "years": -1,
                    "locations": "all",
                    "limit": limit,
                    "offset": offset,
                }
                # 세그먼트별 파라미터 설정
                if "job_group_id" in seg_config:
                    params["job_group_id"] = seg_config["job_group_id"]
                if "job_ids" in seg_config:
                    job_ids = seg_config["job_ids"]
                    if isinstance(job_ids, list):
                        # httpx는 list params를 자동 처리
                        params["job_ids"] = job_ids
                    else:
                        params["job_ids"] = job_ids

                try:
                    resp = await client.get(WANTED_API_BASE, params=params)
                    resp.raise_for_status()
                    data = resp.json()
                except Exception as e:
                    logger.error(f"원티드 API 호출 실패 [{segment_id}]: {e}")
                    self.context.total_errors += 1
                    self.context.errors.append({
                        "segment_id": segment_id,
                        "error": str(e),
                        "phase": "fetch_listings",
                    })
                    break

                jobs = data.get("data", [])
                if not jobs:
                    break

                for job in jobs:
                    listings.append({
                        "external_id": str(job.get("id", "")),
                        "title": job.get("position", job.get("title", "")),
                        "company_name": job.get("company", {}).get("name", ""),
                        "url": f"https://www.wanted.co.kr/wd/{job.get('id', '')}",
                        "segment_id": segment_id,
                    })

                # 페이지네이션: 다음 페이지 확인
                if len(jobs) < limit:
                    break
                offset += limit

                # 최대 200건까지만 수집 (세그먼트당)
                if offset >= 200:
                    break

                await polite_delay()

        self.context.total_fetched += len(listings)
        logger.info(f"원티드 [{segment_id}] {len(listings)}건 목록 수집 완료")
        return listings

    async def fetch_detail(self, listing: dict) -> dict | None:
        """개별 공고 상세 페이지에서 JD 전문 수집"""
        external_id = listing.get("external_id", "")
        if not external_id:
            return None

        detail_url = f"{WANTED_API_BASE}/{external_id}"

        async with get_http_client() as client:
            try:
                resp = await client.get(detail_url)
                resp.raise_for_status()
                data = resp.json()
            except Exception as e:
                logger.error(f"원티드 상세 조회 실패 [id={external_id}]: {e}")
                self.context.total_errors += 1
                return None

        job = data.get("job", data)

        # JD 전문 조합: 포지션 소개 + 주요업무 + 자격요건 + 우대사항 + 혜택 및 복지
        detail_sections = []
        for key in ["position", "intro", "main_tasks", "requirements", "preferred", "benefits"]:
            text = job.get(key, "")
            if text and isinstance(text, str):
                detail_sections.append(text.strip())

        raw_text = "\n\n".join(detail_sections) if detail_sections else ""

        # 연봉 파싱 (원티드 제공 시)
        salary = job.get("salary", {}) or {}

        return {
            **listing,
            "raw_text": raw_text,
            "salary_min": salary.get("min"),
            "salary_max": salary.get("max"),
            "company_name": listing["company_name"],
        }
