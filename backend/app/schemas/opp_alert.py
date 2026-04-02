from app.schemas.common import CamelModel


class OppAlertTrigger(CamelModel):
    otw_increase: float       # 4주 OTW 증가율 (%)
    new_postings: int         # 신규 공고 수
    hiring_weeks: int         # 연속 채용 기간 (주)
    sd_ratio: float           # 현재 세그먼트 S/D Ratio


class OppAlertItem(CamelModel):
    id: str
    company_id: str
    company_name: str
    segment: str
    opp_score: float          # 0~100
    priority: str             # 'CRITICAL' | 'HIGH' | 'MEDIUM'
    triggers: OppAlertTrigger
    detected_at: str          # ISO datetime string


class OppAlertListResponse(CamelModel):
    items: list[OppAlertItem]
    total: int
    generated_at: str
