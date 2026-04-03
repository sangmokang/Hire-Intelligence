"""TDS(인재 밀도 점수) 계산 공통 모듈 — candidate_profiler_service에서 추출"""
from app.schemas.candidate_profiler import SalaryNegotiation


# ---------------------------------------------------------------------------
# 학력 점수 (EDS)
# ---------------------------------------------------------------------------

EDUCATION_SCORES: dict[str, float] = {
    "phd": 95.0,
    "master": 80.0,
    "bachelor_top": 70.0,
    "bachelor": 55.0,
    "other": 40.0,
}

# 상위권 대학 키워드 (학사 기준 tier 구분용)
TOP_UNIVERSITIES = {
    "서울대", "kaist", "포항공대", "postech", "연세대", "고려대",
    "성균관대", "한양대", "서강대", "카이스트",
}


def _classify_education(education: str | None) -> float:
    """학력 텍스트 → EDS 점수"""
    if not education:
        return EDUCATION_SCORES["other"]
    edu_lower = education.lower()
    if "박사" in edu_lower or "ph.d" in edu_lower or "phd" in edu_lower:
        return EDUCATION_SCORES["phd"]
    if "석사" in edu_lower or "master" in edu_lower:
        return EDUCATION_SCORES["master"]
    # 학사 여부 판단 후 상위권 대학 여부로 tier 구분
    is_bachelor = "학사" in edu_lower or "대학" in edu_lower or "bachelor" in edu_lower
    if is_bachelor:
        for univ in TOP_UNIVERSITIES:
            if univ in edu_lower:
                return EDUCATION_SCORES["bachelor_top"]
        return EDUCATION_SCORES["bachelor"]
    return EDUCATION_SCORES["other"]


# ---------------------------------------------------------------------------
# 경력 점수 (CDS)
# ---------------------------------------------------------------------------

COMPANY_TIER_SCORES: dict[str, float] = {
    "tier1": 90.0,
    "tier2": 70.0,
    "tier3": 50.0,
    "startup": 45.0,
    "other": 35.0,
}

TIER1_COMPANIES: set[str] = {
    "카카오", "네이버", "토스", "쿠팡", "삼성전자", "lg전자", "현대차",
    "kakao", "naver", "toss", "coupang",
}
TIER2_COMPANIES: set[str] = {
    "line", "skt", "kt", "lg유플러스", "sk하이닉스", "삼성sds",
}


def _classify_company_tier(company: str | None) -> str:
    if not company:
        return "other"
    c_lower = company.lower()
    for t1 in TIER1_COMPANIES:
        if t1.lower() in c_lower:
            return "tier1"
    for t2 in TIER2_COMPANIES:
        if t2.lower() in c_lower:
            return "tier2"
    return "other"


def _calculate_cds(company: str | None, years: int | None) -> float:
    """경력 점수 계산: 재직사 티어 + 경력 연수 가중"""
    tier = _classify_company_tier(company)
    base = COMPANY_TIER_SCORES[tier]
    # 경력 연수 보정: 5년 기준, 최대 +10점
    if years is not None:
        year_bonus = min(years / 5.0, 2.0) * 5.0  # 5년당 5점, 최대 10점
        base = min(base + year_bonus, 100.0)
    return base


# ---------------------------------------------------------------------------
# 전문성 점수 (PDS)
# ---------------------------------------------------------------------------

def _calculate_pds(skills: list[str] | None) -> float:
    """스킬 수 기반 전문성 점수"""
    base = min(len(skills or []) * 8, 60)
    return min(float(base) + 30.0, 100.0)  # 최소 30점 보장


# ---------------------------------------------------------------------------
# TDS 통합 계산
# ---------------------------------------------------------------------------

def _calculate_tds(education_score: float, career_score: float, skill_score: float) -> float:
    return round(education_score * 0.45 + career_score * 0.35 + skill_score * 0.20, 1)


def _tds_grade(tds: float) -> str:
    if tds >= 85:
        return "S"
    elif tds >= 70:
        return "A"
    elif tds >= 55:
        return "B"
    elif tds >= 40:
        return "C"
    return "D"


def _tds_percentile(tds: float) -> float:
    """TDS 점수 → 상위 N% (간단 선형 추정)"""
    # TDS 50점 = 상위 50%, 100점 = 상위 1%
    pct = max(1.0, 100.0 - tds)
    return round(pct, 1)


# ---------------------------------------------------------------------------
# 연봉 협상력
# ---------------------------------------------------------------------------

# 세그먼트별 기본 연봉 범위 (만원, 5년차 기준): P25, P50, P75
SEGMENT_SALARY: dict[str, tuple[int, int, int]] = {
    "default":  (5000, 7000, 9000),
    "ai-ml":    (7000, 9500, 13000),
    "backend":  (5500, 7500, 10000),
    "data":     (6000, 8000, 11000),
    "frontend": (5000, 7000, 9500),
    "mobile":   (5500, 7500, 10000),
    "devops":   (6000, 8500, 11000),
}


def _salary_negotiation(tds: float, segment: str | None) -> SalaryNegotiation:
    p25, p50, p75 = SEGMENT_SALARY.get(segment or "default", SEGMENT_SALARY["default"])
    leverage = "HIGH" if tds >= 75 else ("MEDIUM" if tds >= 55 else "LOW")
    return SalaryNegotiation(
        market_p25=p25,
        market_p50=p50,
        market_p75=p75,
        recommended_leverage=leverage,
    )
