"""TDS 시뮬레이터 서비스 — CHRO 전용 채용 조직 인재 밀도 시뮬레이션"""
from app.schemas.tds_simulator import TdsSimulatorRequest, TdsSimulatorResponse
from app.services.tds_calculator import (
    _classify_education,
    _calculate_cds,
    _calculate_pds,
    _calculate_tds,
    _tds_grade,
    _tds_percentile,
)

# 업계 평균 TDS (벤치마크)
INDUSTRY_BENCHMARK: dict[str, float] = {
    "default":  65.0,
    "ai-ml":    72.0,
    "backend":  68.0,
    "data":     70.0,
    "frontend": 64.0,
    "mobile":   65.0,
    "devops":   67.0,
}


def _build_benchmark_comparison(tds: float, segment: str | None) -> str:
    avg = INDUSTRY_BENCHMARK.get(segment or "default", INDUSTRY_BENCHMARK["default"])
    delta = round(tds - avg, 1)
    if delta > 5:
        return f"업계 평균({avg}점) 대비 {delta}점 높은 우수 수준입니다."
    elif delta < -5:
        return f"업계 평균({avg}점) 대비 {abs(delta)}점 낮습니다. 인재 밀도 강화가 필요합니다."
    return f"업계 평균({avg}점)과 유사한 수준입니다."


_FALLBACK_RECS = [
    "현재 인재 풀의 강점을 유지하면서 약점 분야를 보완하세요.",
    "정기적인 역량 평가를 통해 인재 밀도 변화를 추적하세요.",
    "온보딩 프로세스를 강화하여 신규 입사자의 빠른 적응을 지원하세요.",
]


def _build_recommendations(eds: float, cds: float, pds: float, grade: str) -> list[str]:
    recs = []
    if eds < 65:
        recs.append("학력 요건을 높여 석사 이상 후보자 비율을 늘리세요.")
    if cds < 65:
        recs.append("Tier1 기업 출신 인재 비중을 높이거나 경력 기준을 강화하세요.")
    if pds < 65:
        recs.append("기술 스택 다양성 강화를 위해 전문 스킬 보유자를 우대하세요.")
    if grade in ("C", "D"):
        recs.append("핵심 포지션에 외부 인재 영입 또는 내부 육성 트랙을 강화하세요.")
    # fallback으로 3개 보장
    for fb in _FALLBACK_RECS:
        if len(recs) >= 3:
            break
        if fb not in recs:
            recs.append(fb)
    return recs[:3]


class TdsSimulatorService:
    def simulate(self, req: TdsSimulatorRequest) -> TdsSimulatorResponse:
        eds = _classify_education(req.education)
        cds = _calculate_cds(req.current_company, req.years_of_experience)
        pds = _calculate_pds(req.skills)
        tds = _calculate_tds(eds, cds, pds)
        grade = _tds_grade(tds)
        percentile = _tds_percentile(tds)
        benchmark = _build_benchmark_comparison(tds, req.target_segment)
        recommendations = _build_recommendations(eds, cds, pds, grade)
        return TdsSimulatorResponse(
            tds_score=tds,
            eds_score=round(eds, 1),
            cds_score=round(cds, 1),
            pds_score=round(pds, 1),
            grade=grade,
            percentile=percentile,
            benchmark_comparison=benchmark,
            recommendations=recommendations,
        )
