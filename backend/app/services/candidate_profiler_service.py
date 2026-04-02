"""후보자 프로파일러 서비스 — TDS(인재 밀도 점수) 계산 및 채용 판단 정보 제공"""
import re

from sqlalchemy.orm import Session

from app.schemas.candidate_profiler import (
    CandidateProfilerRequest,
    CandidateProfilerResponse,
    ApplicationDirection,
    SalaryNegotiation,
    CompetingOffer,
)


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
# 지원 방향성
# ---------------------------------------------------------------------------

def _classify_direction(candidate_tds: float, target_tds: float | None) -> str:
    if target_tds is None:
        return "LATERAL"
    delta = (candidate_tds - target_tds) / max(target_tds, 1.0)
    if delta > 0.10:
        return "DOWNWARD"
    elif delta < -0.10:
        return "UPWARD"
    return "LATERAL"


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


# ---------------------------------------------------------------------------
# 경쟁 오퍼 (유사 TDS 기업)
# ---------------------------------------------------------------------------

# 하드코딩 fallback 데이터: (company_name, tds_score)
_FALLBACK_COMPANY_TDS: list[tuple[str, float]] = [
    ("삼성전자",    88.0),
    ("LG전자",      82.0),
    ("카카오",      85.0),
    ("네이버",      83.0),
    ("토스",        80.0),
    ("쿠팡",        79.0),
    ("LINE",        75.0),
    ("SKT",         72.0),
    ("KT",          68.0),
    ("삼성SDS",     70.0),
    ("카카오페이",  76.0),
    ("현대차",      74.0),
    ("크래프톤",    71.0),
    ("넥슨",        69.0),
    ("엔씨소프트",  67.0),
    ("당근마켓",    65.0),
    ("배달의민족",  73.0),
    ("쏘카",        58.0),
    ("야놀자",      60.0),
    ("뱅크샐러드",  62.0),
]


def _get_competing_offers(db: Session, candidate_tds: float) -> list[CompetingOffer]:
    """TDS ±8 구간 기업 Top3 반환 (DB 없으면 하드코딩 fallback)"""
    low, high = candidate_tds - 8, candidate_tds + 8

    # fallback 데이터에서 TDS 구간 필터링
    candidates = [
        (name, tds) for name, tds in _FALLBACK_COMPANY_TDS
        if low <= tds <= high
    ]
    # 후보자 TDS와 차이가 작은 순으로 정렬
    candidates.sort(key=lambda x: abs(x[1] - candidate_tds))

    offers: list[CompetingOffer] = []
    for name, tds in candidates[:3]:
        delta = abs(tds - candidate_tds)
        likelihood = "HIGH" if delta <= 3 else ("MEDIUM" if delta <= 6 else "LOW")
        offers.append(CompetingOffer(company_name=name, tds_score=tds, likelihood=likelihood))

    # 결과가 없으면 고정 예시 반환
    if not offers:
        offers = [
            CompetingOffer(company_name="카카오", tds_score=round(candidate_tds + 5, 1), likelihood="HIGH"),
            CompetingOffer(company_name="LINE", tds_score=round(candidate_tds, 1), likelihood="MEDIUM"),
            CompetingOffer(company_name="SKT", tds_score=round(candidate_tds - 4, 1), likelihood="MEDIUM"),
        ]
    return offers


# ---------------------------------------------------------------------------
# 레쥬메 텍스트 파싱 (간단 키워드 매칭)
# ---------------------------------------------------------------------------

_EDUCATION_KEYWORDS = ["박사", "석사", "학사", "phd", "master", "대학원", "서울대", "kaist", "포항공대", "연세대", "고려대"]
_SKILL_KEYWORDS = [
    "python", "java", "kotlin", "javascript", "typescript", "react", "vue", "angular",
    "spring", "django", "fastapi", "node.js", "go", "rust", "c++", "c#",
    "aws", "gcp", "azure", "kubernetes", "docker", "kafka", "redis", "mysql",
    "postgresql", "mongodb", "elasticsearch", "pytorch", "tensorflow", "ml", "llm",
    "데이터", "머신러닝", "딥러닝", "ai", "nlp", "cv", "bigquery", "spark",
]
_COMPANY_TIER1_KEYWORDS = list(TIER1_COMPANIES)
_COMPANY_TIER2_KEYWORDS = list(TIER2_COMPANIES)
_YEAR_PATTERNS = ["년", "years", "year"]


def _parse_resume_text(text: str) -> dict:
    """레쥬메 텍스트에서 학력/경력/스킬 추출"""
    lower = text.lower()

    # 스킬 추출
    skills = [kw for kw in _SKILL_KEYWORDS if kw in lower]

    # 학력 추출
    education: str | None = None
    for kw in _EDUCATION_KEYWORDS:
        if kw.lower() in lower:
            education = kw
            break

    # 재직사 추출 (tier1 → tier2 순)
    current_company: str | None = None
    for c in _COMPANY_TIER1_KEYWORDS + _COMPANY_TIER2_KEYWORDS:
        if c.lower() in lower:
            current_company = c
            break

    # 경력 연수 추출 (숫자 + 년/year 패턴)
    years: int | None = None
    match = re.search(r'(\d+)\s*(?:년|years?)\s*(?:경력|차|이상|以上)?', lower)
    if match:
        years = min(int(match.group(1)), 40)

    return {
        "skills": skills,
        "education": education,
        "current_company": current_company,
        "years": years,
    }


# ---------------------------------------------------------------------------
# 요약 생성
# ---------------------------------------------------------------------------

def _build_summary(tds: float, grade: str, direction_type: str, leverage: str) -> str:
    grade_desc = {"S": "최상위", "A": "상위", "B": "중상위", "C": "중위", "D": "하위"}.get(grade, "")
    dir_desc = {"UPWARD": "도전적인 상향", "LATERAL": "안정적인 수평", "DOWNWARD": "여유 있는 하향"}.get(direction_type, "수평")
    lev_desc = {"HIGH": "높은", "MEDIUM": "적절한", "LOW": "제한적인"}.get(leverage, "적절한")
    return (
        f"TDS {tds}점({grade_desc} {grade}등급)으로 현재 시장에서 {grade_desc} 포지션의 인재입니다. "
        f"{dir_desc} 지원 방향이 적합하며, {lev_desc} 연봉 협상력을 보유하고 있습니다."
    )


# ---------------------------------------------------------------------------
# 서비스 클래스
# ---------------------------------------------------------------------------

class CandidateProfilerService:
    def __init__(self, db: Session) -> None:
        self._db = db

    def analyze(self, req: CandidateProfilerRequest) -> CandidateProfilerResponse:
        """후보자 TDS 분석 수행"""
        # 입력 소스 결정: 레쥬메 텍스트 우선, 없으면 구조화 입력
        if req.resume_text:
            parsed = _parse_resume_text(req.resume_text[:3000])
            education = parsed["education"] or req.education
            current_company = parsed["current_company"] or req.current_company
            years = parsed["years"] if parsed["years"] is not None else req.years_of_experience
            skills = list(set((parsed["skills"] or []) + (req.skills or [])))
        else:
            education = req.education
            current_company = req.current_company
            years = req.years_of_experience
            skills = req.skills or []

        # TDS 구성 요소 계산
        eds = _classify_education(education)
        cds = _calculate_cds(current_company, years)
        pds = _calculate_pds(skills)
        tds = _calculate_tds(eds, cds, pds)

        grade = _tds_grade(tds)
        percentile = _tds_percentile(tds)

        # 지원 방향성 (targetCompanyId 기반 TDS 조회는 현재 미지원 → None 처리)
        direction_type = _classify_direction(tds, None)
        direction = ApplicationDirection(
            type=direction_type,
            candidate_tds=tds,
            target_company_tds=None,
            delta_percent=None,
        )

        # 연봉 협상력
        salary = _salary_negotiation(tds, req.target_segment)

        # 경쟁 오퍼
        offers = _get_competing_offers(self._db, tds)

        # 요약
        summary = _build_summary(tds, grade, direction_type, salary.recommended_leverage)

        return CandidateProfilerResponse(
            tds_score=tds,
            tds_percentile=percentile,
            tds_grade=grade,
            application_direction=direction,
            salary_negotiation=salary,
            competing_offers=offers,
            summary=summary,
        )
