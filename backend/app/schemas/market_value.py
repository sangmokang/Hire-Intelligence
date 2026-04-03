from app.schemas.common import CamelModel


class MarketValueRequest(CamelModel):
    skills: list[str] | None = None
    education: str | None = None
    years_of_experience: int | None = None
    current_company: str | None = None
    target_segment: str | None = None    # "backend", "ai-ml" 등


class MarketValueResponse(CamelModel):
    estimated_value_p25: int    # 만원 단위
    estimated_value_p50: int
    estimated_value_p75: int
    tds_score: float
    tds_grade: str              # 'S' | 'A' | 'B' | 'C' | 'D'
    tds_percentile: float       # 상위 N%
    segment_rank: str           # "상위 X% 수준"
    value_drivers: list[str]    # 강점 요소 (최대 3개)
    improvement_tips: list[str] # 개선 팁 (최대 3개)
