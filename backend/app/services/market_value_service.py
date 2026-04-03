"""시장가치 서비스 — JOB_SEEKER 전용 스킬/경력 기반 연봉 시장가치 계산"""
from app.schemas.market_value import MarketValueRequest, MarketValueResponse
from app.services.tds_calculator import (
    _classify_education,
    _calculate_cds,
    _calculate_pds,
    _calculate_tds,
    _tds_grade,
    _tds_percentile,
    SEGMENT_SALARY,
)


def _get_value_drivers(eds: float, cds: float, pds: float) -> list[str]:
    """강점 요소 추출"""
    drivers = []
    if eds >= 70:
        drivers.append("높은 학력 배경이 연봉 협상력을 높입니다.")
    if cds >= 70:
        drivers.append("우수한 재직사 경력이 시장가치를 향상시킵니다.")
    if pds >= 70:
        drivers.append("다양한 기술 스택이 경쟁력을 높입니다.")
    if not drivers:
        drivers.append("기본적인 시장 경쟁력을 보유하고 있습니다.")
    return drivers[:3]


def _get_improvement_tips(eds: float, cds: float, pds: float) -> list[str]:
    """개선 팁 생성"""
    tips = []
    if eds < 65:
        tips.append("석사 이상 학위 취득 또는 전문 자격증으로 학력 가치를 높이세요.")
    if cds < 65:
        tips.append("Tier1 기업으로의 이직 경험이 연봉 협상력을 크게 향상시킵니다.")
    if pds < 65:
        tips.append("인기 기술 스택(AI/ML, 클라우드 등) 추가 학습으로 전문성을 높이세요.")
    if not tips:
        tips.append("현재 강점을 유지하면서 시장 수요 높은 스킬을 지속 업데이트하세요.")
    return tips[:3]


def _get_segment_rank(tds: float) -> str:
    if tds >= 85:
        return "상위 15% 수준"
    elif tds >= 70:
        return "상위 30% 수준"
    elif tds >= 55:
        return "상위 50% 수준"
    elif tds >= 40:
        return "상위 60% 수준"
    return "하위 40% 수준"


class MarketValueService:
    def calculate(self, req: MarketValueRequest) -> MarketValueResponse:
        eds = _classify_education(req.education)
        cds = _calculate_cds(req.current_company, req.years_of_experience)
        pds = _calculate_pds(req.skills)
        tds = _calculate_tds(eds, cds, pds)
        grade = _tds_grade(tds)
        percentile = _tds_percentile(tds)

        # 연봉 범위 (TDS 기반 보정)
        p25, p50, p75 = SEGMENT_SALARY.get(req.target_segment or "default", SEGMENT_SALARY["default"])
        # TDS 보정: 70점 기준, 5점 차이마다 ±5% 조정
        tds_factor = 1.0 + (tds - 70.0) / 100.0
        adjusted_p25 = round(p25 * tds_factor / 100) * 100
        adjusted_p50 = round(p50 * tds_factor / 100) * 100
        adjusted_p75 = round(p75 * tds_factor / 100) * 100

        return MarketValueResponse(
            estimated_value_p25=max(adjusted_p25, 3000),
            estimated_value_p50=max(adjusted_p50, 4000),
            estimated_value_p75=max(adjusted_p75, 5000),
            tds_score=tds,
            tds_grade=grade,
            tds_percentile=percentile,
            segment_rank=_get_segment_rank(tds),
            value_drivers=_get_value_drivers(eds, cds, pds),
            improvement_tips=_get_improvement_tips(eds, cds, pds),
        )
