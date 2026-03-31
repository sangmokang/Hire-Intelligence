from datetime import datetime

from app.schemas.common import CamelModel


class WeeklyCollectionStats(CamelModel):
    """주간 수집 통계"""
    week: str                   # "2026-W13" 형식
    total_postings: int         # 해당 주 총 채용 공고 수
    total_companies: int        # 해당 주 채용한 기업 수
    segments_covered: int       # 14개 직군 중 데이터 있는 직군 수
    segments_total: int         # 항상 14


class AnomalyItem(CamelModel):
    """이상치 항목 — 전주 대비 ±50% 변동"""
    week: str
    prev_week: str
    prev_total_postings: int
    curr_total_postings: int
    change_pct: float


class DataQualityResponse(CamelModel):
    """데이터 품질 모니터링 응답"""
    current_week: str                           # 현재 주 (ISO 형식)
    weekly_stats: list[WeeklyCollectionStats]   # 최근 4주 통계
    missing_segments: list[str]                 # 이번 주 데이터 없는 직군명
    anomalies: list[AnomalyItem]                # 전주 대비 ±50% 변동 항목


class CrawlStatusResponse(CamelModel):
    """크롤 상태 응답"""
    last_crawl_at: datetime | None      # 마지막 크롤 실행 시각
    last_crawl_status: str | None       # "completed" / "failed" / "running"
    total_crawled: int                  # 마지막 크롤 총 수집 수
    total_parsed: int                   # 마지막 크롤 총 파싱 수
    next_scheduled: str                 # 정적 스케줄 정보
