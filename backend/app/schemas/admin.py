from datetime import datetime
from typing import Optional

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


# ── 유저 관리 스키마 ──────────────────────────────────────────────────────────

class AdminUserDetail(CamelModel):
    """관리자 유저 상세 정보"""
    user_id: str
    email: Optional[str] = None
    name: Optional[str] = None
    role: str
    plan: str
    status: str
    company: Optional[str] = None
    job_title: Optional[str] = None
    login_count: int = 0
    last_login_at: Optional[str] = None
    created_at: Optional[str] = None
    # 구독 이력 (최근 구독 정보)
    subscription_plan: Optional[str] = None
    subscription_status: Optional[str] = None
    subscription_started_at: Optional[str] = None
    subscription_expires_at: Optional[str] = None


class AdminUserListResponse(CamelModel):
    """유저 목록 응답 (페이지네이션)"""
    users: list[AdminUserDetail]
    total: int
    offset: int
    limit: int


class AdminUserUpdateRequest(CamelModel):
    """유저 정보 수정 요청"""
    role: Optional[str] = None      # USER / ADMIN / SUPER_ADMIN
    status: Optional[str] = None    # ACTIVE / SUSPENDED / BLOCKED
    plan: Optional[str] = None      # STARTER / PRO / ENTERPRISE


# ── 과금 관리 스키마 ──────────────────────────────────────────────────────────

class PlanStat(CamelModel):
    """플랜별 사용자 수"""
    plan: str
    count: int


class BillingSummaryResponse(CamelModel):
    """과금 요약 응답"""
    plan_stats: list[PlanStat]      # 플랜별 유저 수
    total_users: int


class PaymentItem(CamelModel):
    """결제 내역 항목"""
    id: str
    user_id: str
    user_email: Optional[str] = None
    amount: int
    plan: str
    status: str
    paid_at: Optional[str] = None
    created_at: Optional[str] = None


class BillingPaymentsResponse(CamelModel):
    """결제 내역 응답"""
    payments: list[PaymentItem]
    total: int
    offset: int
    limit: int
