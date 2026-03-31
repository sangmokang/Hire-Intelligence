"""Company DNA 관련 Pydantic 스키마"""
from app.schemas.common import CamelModel


class TechItem(CamelModel):
    name: str
    count: int
    pct: float


class TechDna(CamelModel):
    """기술 프로필 DNA"""
    stack_count: int
    diversity_index: float    # Shannon diversity (0-5 scale)
    diversity_score: float    # 세그먼트 백분위 (0-100)
    top_techs: list[TechItem]


class HiringDna(CamelModel):
    """채용 패턴 DNA"""
    total_postings: int
    growth_velocity: float | None    # null = 4주 미만 데이터
    growth_label: str                # "급성장" | "성장" | "안정" | "감소" | "데이터 부족"
    intensity_score: float           # 세그먼트 백분위 (0-100)
    role_distribution: dict[str, int]
    segment_breadth: int


class CompensationDna(CamelModel):
    """보상 벤치마크 DNA"""
    salary_avg: int | None           # 만원 단위
    salary_min: int | None
    salary_max: int | None
    position_percentile: float | None
    position_label: str              # "상위 25%" | "평균 수준" | "하위 40%" | "데이터 없음"
    equity_ratio: float
    benefits_count: int
    top_benefits: list[str]


class CultureSignals(CamelModel):
    """조직 문화 시그널"""
    growth_stage: str | None         # startup/scale-up/enterprise
    new_position_ratio: float
    team_size_patterns: list[str]
    culture_score: float             # 복합 점수 (0-100)


class CompanyDnaResponse(CamelModel):
    """회사 DNA 전체 응답"""
    company_id: str
    company_name: str
    segment_id: str | None
    week: str
    overall_score: float
    tech: TechDna
    hiring: HiringDna
    compensation: CompensationDna
    culture: CultureSignals


class SegmentBenchmarkResponse(CamelModel):
    """세그먼트 벤치마크 (비교 기준선)"""
    segment_id: str
    segment_name: str
    avg_tech_score: float
    avg_hiring_score: float
    avg_salary: int | None
    avg_culture_score: float
    company_count: int


class DnaComparisonResponse(CamelModel):
    """2개 기업 DNA 비교 응답"""
    company_a: CompanyDnaResponse
    company_b: CompanyDnaResponse
    segment_benchmark: SegmentBenchmarkResponse | None


class DnaTrendPoint(CamelModel):
    """DNA 트렌드 단일 데이터 포인트"""
    week: str
    overall_score: float
    tech_score: float
    hiring_score: float
    salary_pct: float | None
    culture_score: float


class DnaTrendResponse(CamelModel):
    """DNA 트렌드 응답"""
    company_id: str
    company_name: str
    segment_id: str | None
    data_points: list[DnaTrendPoint]
