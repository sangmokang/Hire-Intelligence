from app.schemas.common import CamelModel


class CandidateProfilerRequest(CamelModel):
    # 방식 1: 레쥬메 텍스트 (자유형)
    resume_text: str | None = None       # 최대 3000자

    # 방식 2: 구조화 입력
    current_company: str | None = None
    years_of_experience: int | None = None  # 0~40
    education: str | None = None            # "서울대 컴퓨터공학" 형태
    skills: list[str] | None = None

    # 컨텍스트
    target_segment: str | None = None    # 세그먼트 ID ("backend", "ai-ml" 등)
    target_company_id: str | None = None  # 지원 회사


class SalaryNegotiation(CamelModel):
    market_p25: int   # 만원 단위
    market_p50: int
    market_p75: int
    recommended_leverage: str  # 'HIGH' | 'MEDIUM' | 'LOW'


class ApplicationDirection(CamelModel):
    type: str       # 'UPWARD' | 'LATERAL' | 'DOWNWARD'
    candidate_tds: float
    target_company_tds: float | None = None
    delta_percent: float | None = None


class CompetingOffer(CamelModel):
    company_name: str
    tds_score: float
    likelihood: str  # 'HIGH' | 'MEDIUM' | 'LOW'


class CandidateProfilerResponse(CamelModel):
    tds_score: float              # 0~100
    tds_percentile: float         # 상위 N%
    tds_grade: str                # 'S' | 'A' | 'B' | 'C' | 'D'
    application_direction: ApplicationDirection
    salary_negotiation: SalaryNegotiation
    competing_offers: list[CompetingOffer]
    summary: str                  # 1-2문장 종합 평가
