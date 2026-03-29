"""JD 분석 관련 Pydantic 스키마"""
from datetime import datetime
from pydantic import Field
from app.schemas.common import CamelModel


class TechTrend(CamelModel):
    """기술 스택 트렌드"""
    name: str
    count: int
    previous_count: int = 0
    change: int = 0  # week-over-week 변화량


class ExperienceDistribution(CamelModel):
    """경력 수준 분포"""
    level: str  # junior/mid/senior/lead/exec
    count: int
    percentage: float = 0.0


class SalaryBenchmark(CamelModel):
    """세그먼트별 연봉 벤치마크"""
    segment_id: str
    segment_name: str
    salary_min: int | None = None
    salary_max: int | None = None
    salary_avg: int | None = None
    sample_count: int = 0


class DomainTag(CamelModel):
    """도메인 태그"""
    name: str
    count: int


class JdInsightsResponse(CamelModel):
    """JD 인사이트 응답"""
    tech_trends: list[TechTrend] = []
    experience_distribution: list[ExperienceDistribution] = []
    salary_benchmarks: list[SalaryBenchmark] = []
    top_domain_tags: list[DomainTag] = []
    total_analyzed: int = 0


class JdParsedData(CamelModel):
    """LLM 파싱 결과 — 6개 카테고리"""
    tech_stack: list[str] = []
    experience: dict | None = None  # {min_years, max_years, level}
    compensation: dict | None = None  # {salary_min, salary_max, has_equity, benefits}
    role_keywords: list[str] = []
    domain_knowledge: list[str] = []
    org_signals: dict | None = None  # {team_size, is_new_position, growth_stage}


class JdAnalysisResponse(CamelModel):
    """JD 분석 단건 응답"""
    id: str
    position_id: str | None = None
    segment_id: str
    platform: str
    week: str
    parsed_data: JdParsedData | None = None
    tech_stacks: list[str] = []
    experience_min: int | None = None
    experience_max: int | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    role_level: str | None = None
    domain_tags: list[str] = []
    model_used: str | None = None
    parsed_at: datetime | None = None


class CrawlTriggerRequest(CamelModel):
    """크롤 트리거 요청"""
    platform: str = Field(..., pattern="^(wanted|saramin|all)$", description="크롤링 대상 플랫폼")
    segment_id: str | None = Field(None, description="특정 세그먼트만 크롤링 (null = 전체)")


class CrawlTriggerResponse(CamelModel):
    """크롤 트리거 응답"""
    crawl_run_id: str
    status: str = "running"
    message: str = "크롤링이 시작되었습니다."


class CrawlStatusResponse(CamelModel):
    """크롤 상태 응답"""
    crawl_run_id: str
    status: str
    platform: str
    segment_id: str | None = None
    total_fetched: int = 0
    total_parsed: int = 0
    total_errors: int = 0
    started_at: datetime | None = None
    finished_at: datetime | None = None
