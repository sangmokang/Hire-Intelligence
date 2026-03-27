from datetime import datetime
from pydantic import Field
from typing import Any

from app.schemas.common import CamelModel


class DashboardMetadata(CamelModel):
    """대시보드 메타데이터 (최신 데이터 기준 주차/시각)"""
    latest_week: str | None = None
    updated_at: datetime | None = None


class SegmentData(CamelModel):
    """직군 수급 데이터 (SDMatrixItem)"""
    segment_id: str
    segment_name: str
    demand: int
    supply: int
    sd_ratio: float
    otw_pct: float
    quadrant: str  # OPPORTUNITY | COMPETITIVE | OVERSUPPLY | NICHE
    avg_salary: float | None = None
    trend: str | None = None  # "up" | "down" | "stable"


class DashboardSummary(CamelModel):
    """대시보드 요약"""
    total_postings: int
    opportunity_segments: int
    avg_sd_ratio: float
    top_opportunity_segment: str


class SDMatrixResponse(CamelModel):
    """수급 매트릭스 응답"""
    summary: DashboardSummary
    segments: list[SegmentData]


class DrilldownResponse(CamelModel):
    """직군 드릴다운 상세 응답"""
    segment_id: str
    segment_name: str
    week: str
    demand: int
    supply: int
    sd_ratio: float
    otw_pct: float
    avg_salary: float | None = None
    top_companies: list[dict] = []
    weekly_trend: list[dict] = []


class CompanyRankItem(CamelModel):
    """기업 순위 아이템 (FE CompanyRankItem)"""
    company_id: str
    rank: int
    company: str
    segment: str
    weekly_count: int
    positions: list[str] = []
    week_over_week_change: int = 0


class TimelineDataPoint(CamelModel):
    """타임라인 데이터 포인트"""
    week: str
    count: int


class CompanyTimeline(CamelModel):
    """기업 타임라인 (FE CompanyTimeline)"""
    company_id: str
    company: str
    data: list[TimelineDataPoint] = []


class TrendDataPoint(CamelModel):
    """트렌드 데이터 포인트 (FE TrendDataPoint)"""
    week: str
    count: int


class SegmentTrend(CamelModel):
    """세그먼트 트렌드 (FE SegmentTrend)"""
    segment_id: str
    segment_name: str
    data: list[TrendDataPoint] = []


class ResumeMatchRequest(CamelModel):
    """이력서 매칭 요청 (FE ResumeMatchInput)"""
    resume_text: str = Field(min_length=10)
    preferred_segments: list[str] = []
    min_score: float = 0.0
    max_results: int = 10


class MatchResult(CamelModel):
    """매칭 결과 (FE MatchResult)"""
    company_id: str
    company: str
    score: float
    segment: str
    match_reason: str
    matched_skills: list[str] = []
    active_postings: int = 0


class ResumeMatchOutput(CamelModel):
    """이력서 매칭 출력 (FE ResumeMatchOutput)"""
    matches: list[MatchResult] = []
    extracted_keywords: list[str] = []
    processing_time_ms: int = 0
    match_engine: str = "KEYWORD"  # KEYWORD | SEMANTIC


class TalentDensity(CamelModel):
    """인재 밀도 지표"""
    overall: float
    tech_diversity: float
    senior_ratio: float
    avg_tenure: str
    internal_otw_pct: float


class HiringPower(CamelModel):
    """채용 파워 지표"""
    overall: float
    active_postings: int
    weekly_trend: list[float] = []


class CompanyProfile(CamelModel):
    """기업 프로필 (FE CompanyProfile)"""
    company_id: str
    name: str
    talent_density: TalentDensity
    hiring_power: HiringPower
