from app.schemas.common import CamelModel


class TdsSimulatorRequest(CamelModel):
    education: str | None = None          # "서울대 컴퓨터공학 학사" 형태
    current_company: str | None = None    # 현재 재직사
    years_of_experience: int | None = None  # 0~40
    skills: list[str] | None = None
    team_size: int | None = None          # 조직 팀 규모 (선택)
    target_segment: str | None = None    # "backend", "ai-ml" 등


class TdsSimulatorResponse(CamelModel):
    tds_score: float           # 0~100
    eds_score: float           # EDS (학력)
    cds_score: float           # CDS (경력)
    pds_score: float           # PDS (전문성)
    grade: str                 # 'S' | 'A' | 'B' | 'C' | 'D'
    percentile: float          # 상위 N%
    benchmark_comparison: str  # 업계 평균 대비 설명 문장
    recommendations: list[str] # 개선 추천 리스트 (3개)
