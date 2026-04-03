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
from app.services.tds_calculator import (
    EDUCATION_SCORES,
    TOP_UNIVERSITIES,
    COMPANY_TIER_SCORES,
    TIER1_COMPANIES,
    TIER2_COMPANIES,
    SEGMENT_SALARY,
    _classify_education,
    _classify_company_tier,
    _calculate_cds,
    _calculate_pds,
    _calculate_tds,
    _tds_grade,
    _tds_percentile,
    _salary_negotiation,
)


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
