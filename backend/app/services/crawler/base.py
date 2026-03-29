"""크롤러 기본 클래스 및 유틸리티"""
import re
import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

# 회사명 정규화용 접미사 패턴
_COMPANY_SUFFIXES = re.compile(
    r'\s*\(?(주|株|Inc\.?|Corp\.?|Co\.?\s*,?\s*Ltd\.?|LLC|Ltd\.?|SA|GmbH)\)?\s*$',
    re.IGNORECASE,
)


@dataclass
class CrawlContext:
    """크롤 실행 컨텍스트 — 실행 통계 추적"""
    total_fetched: int = 0
    total_new: int = 0
    total_skipped: int = 0
    total_errors: int = 0
    errors: list[dict] = field(default_factory=list)


def normalize_company_name(name: str) -> str:
    """회사명 정규화 — 접미사 제거 및 공백 정리"""
    name = name.strip()
    name = _COMPANY_SUFFIXES.sub('', name).strip()
    # 연속 공백 제거
    name = re.sub(r'\s+', ' ', name)
    return name


def jaccard_similarity(a: str, b: str) -> float:
    """Jaccard 유사도 — 제목 중복 검사용"""
    set_a = set(a.lower().split())
    set_b = set(b.lower().split())
    if not set_a or not set_b:
        return 0.0
    intersection = set_a & set_b
    union = set_a | set_b
    return len(intersection) / len(union)


def is_duplicate_title(new_title: str, existing_titles: list[str], threshold: float = 0.8) -> bool:
    """기존 제목과 Jaccard >= threshold이면 중복으로 판정"""
    for existing in existing_titles:
        if jaccard_similarity(new_title, existing) >= threshold:
            return True
    return False


async def polite_delay():
    """크롤링 사이의 예의 딜레이"""
    await asyncio.sleep(settings.CRAWL_DELAY_SECONDS)


def get_http_client() -> httpx.AsyncClient:
    """브라우저 유사 헤더를 가진 HTTP 클라이언트"""
    return httpx.AsyncClient(
        timeout=30.0,
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/html, */*",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8",
        },
        follow_redirects=True,
    )


class BaseCrawler(ABC):
    """크롤러 추상 기본 클래스"""

    def __init__(self):
        self.context = CrawlContext()

    @abstractmethod
    async def fetch_listings(self, segment_id: str) -> list[dict]:
        """세그먼트별 채용공고 목록 수집"""
        ...

    @abstractmethod
    async def fetch_detail(self, listing: dict) -> dict | None:
        """개별 공고 상세 정보 + JD 텍스트 수집"""
        ...

    @property
    @abstractmethod
    def platform_name(self) -> str:
        """플랫폼 이름 (wanted/saramin)"""
        ...
