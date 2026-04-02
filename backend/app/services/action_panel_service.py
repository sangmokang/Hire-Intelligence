"""Action Panel 서비스 — rule-based insight/actions 생성 (Claude API ready 구조)"""
from app.schemas.action_panel import (
    ActionPanelRequest,
    ActionPanelResponse,
    ActionItem,
)

# SD Matrix view용 — 시장 상황별 × 사용자 카테고리별 인사이트
SD_MATRIX_INSIGHTS: dict[str, dict[str, str]] = {
    "RED": {  # ratio < 0.5
        "HEADHUNTER": "공급이 부족한 시장입니다. 이 세그먼트에서 클라이언트에게 S/D 데이터를 제시하면 수임료 상향 협상이 가능합니다.",
        "INHOUSE_HR": "공급 부족 시장입니다. 파이프라인을 즉시 확장하고 JD 리라이팅으로 응답률을 높이세요.",
        "CHRO": "채용 난이도가 높은 시장입니다. 헤드헌터 수임을 검토하거나 내부 육성 트랙을 강화하세요.",
        "JOB_SEEKER": "지금이 이직 협상력이 가장 높은 구간입니다. 복수 오퍼를 동시 진행하세요.",
    },
    "YELLOW": {  # 0.5 <= ratio < 1.0
        "HEADHUNTER": "균형 시장입니다. 후보자 품질(TDS) 차별화로 클라이언트 신뢰를 높이세요.",
        "INHOUSE_HR": "표준 채용 전략이 유효합니다. 4주 추세를 주시하며 파이프라인을 유지하세요.",
        "CHRO": "균형 시장입니다. 현재 채용 채널을 유지하되 내부 육성과 병행하세요.",
        "JOB_SEEKER": "적정 경쟁 구간입니다. 차별화된 포트폴리오와 빠른 지원 속도가 핵심입니다.",
    },
    "GREEN": {  # ratio >= 1.0
        "HEADHUNTER": "공급 우위 시장입니다. 이 세그먼트 수임 우선순위를 낮추고 RED 세그먼트에 집중하세요.",
        "INHOUSE_HR": "후보자 공급이 풍부합니다. 직접 채용 채널을 강화하고 면접 기준을 높이세요.",
        "CHRO": "직접 채용이 효율적인 시장입니다. 헤드헌터 예산을 절감하세요.",
        "JOB_SEEKER": "경쟁이 치열합니다. 업계 상위 10% 역량 증명에 집중하거나 인접 세그먼트로 전환을 검토하세요.",
    },
}

# 각 view별 related views 정의
VIEW_RELATED_VIEWS: dict[str, list[str]] = {
    "sd-matrix": ["market-signals", "timeline", "opp-alert"],
    "top-companies": ["company-analysis", "opp-alert", "candidate-profiler"],
    "timeline": ["sd-matrix", "trends"],
    "trends": ["sd-matrix", "timeline"],
    "resume-match": ["candidate-profiler", "market-signals"],
    "company-analysis": ["company-dna", "opp-alert"],
    "market-signals": ["sd-matrix", "opp-alert", "candidate-profiler"],
}

# view별 기본 인사이트 템플릿 (카테고리 무관)
VIEW_DEFAULT_INSIGHTS: dict[str, str] = {
    "sd-matrix": "수급 매트릭스를 분석하여 최적의 채용 전략을 수립하세요.",
    "top-companies": "상위 기업의 채용 동향을 파악하고 타겟 기업을 선정하세요.",
    "timeline": "채용 타임라인을 분석하여 시장 변화를 파악하세요.",
    "trends": "주간 트렌드를 통해 시장 방향성을 예측하세요.",
    "resume-match": "이력서 매칭 결과를 바탕으로 지원 전략을 최적화하세요.",
    "company-analysis": "기업 채용 심층 분석으로 타겟 기업의 채용 패턴을 파악하세요.",
    "market-signals": "시장 시그널을 모니터링하여 기회를 선점하세요.",
}

# view × category 별 actions 정의
VIEW_CATEGORY_ACTIONS: dict[str, dict[str, list[dict]]] = {
    "sd-matrix": {
        "HEADHUNTER": [
            {"priority": "HIGH", "text": "RED 세그먼트 클라이언트에게 S/D 데이터 보고서 발송", "cta": "시장 리포트 보기", "ctaUrl": "/dashboard/market-signals"},
            {"priority": "MEDIUM", "text": "수임료 상향 협상 근거 자료 준비", "cta": None, "ctaUrl": None},
            {"priority": "LOW", "text": "4주 추세 모니터링 설정", "cta": "트렌드 보기", "ctaUrl": "/dashboard/trends"},
        ],
        "INHOUSE_HR": [
            {"priority": "HIGH", "text": "공급 부족 직군 JD 리라이팅으로 지원율 향상", "cta": "JD 인사이트", "ctaUrl": "/dashboard/jd-insights"},
            {"priority": "MEDIUM", "text": "헤드헌터 파트너십 검토", "cta": None, "ctaUrl": None},
            {"priority": "LOW", "text": "채용 파이프라인 현황 점검", "cta": "타임라인", "ctaUrl": "/dashboard/timeline"},
        ],
        "CHRO": [
            {"priority": "HIGH", "text": "채용 난이도 높은 세그먼트 전략 재검토", "cta": None, "ctaUrl": None},
            {"priority": "MEDIUM", "text": "내부 육성 트랙 강화 계획 수립", "cta": None, "ctaUrl": None},
            {"priority": "LOW", "text": "헤드헌터 수임 예산 검토", "cta": None, "ctaUrl": None},
        ],
        "JOB_SEEKER": [
            {"priority": "HIGH", "text": "복수 오퍼 동시 진행 전략 수립", "cta": "기업 비교", "ctaUrl": "/dashboard/company-analysis"},
            {"priority": "MEDIUM", "text": "이력서 키워드 최적화", "cta": "이력서 매칭", "ctaUrl": "/dashboard/resume-match"},
            {"priority": "LOW", "text": "연봉 협상 벤치마크 확인", "cta": "시장 시그널", "ctaUrl": "/dashboard/market-signals"},
        ],
    },
    "top-companies": {
        "HEADHUNTER": [
            {"priority": "HIGH", "text": "채용 급증 기업 클라이언트 유치 타겟 선정", "cta": "기업 분석", "ctaUrl": "/dashboard/company-analysis"},
            {"priority": "MEDIUM", "text": "TOP 기업 채용 담당자 네트워킹", "cta": None, "ctaUrl": None},
            {"priority": "LOW", "text": "기업별 채용 패턴 모니터링", "cta": "타임라인", "ctaUrl": "/dashboard/timeline"},
        ],
        "INHOUSE_HR": [
            {"priority": "HIGH", "text": "경쟁사 채용 현황 벤치마킹", "cta": "기업 DNA", "ctaUrl": "/dashboard/company-dna"},
            {"priority": "MEDIUM", "text": "채용 활성 기업 대상 인재풀 구축", "cta": None, "ctaUrl": None},
            {"priority": "LOW", "text": "업계 평균 대비 우리 회사 포지션 확인", "cta": None, "ctaUrl": None},
        ],
        "CHRO": [
            {"priority": "HIGH", "text": "동종업계 TOP 기업 채용 전략 분석", "cta": "기업 비교", "ctaUrl": "/dashboard/company-analysis"},
            {"priority": "MEDIUM", "text": "인재 유출 위험 기업 모니터링", "cta": None, "ctaUrl": None},
            {"priority": "LOW", "text": "채용 트렌드 기반 인력 계획 수립", "cta": "트렌드", "ctaUrl": "/dashboard/trends"},
        ],
        "JOB_SEEKER": [
            {"priority": "HIGH", "text": "채용 급증 기업 즉시 지원", "cta": "기회 알림", "ctaUrl": "/dashboard/opp-alert"},
            {"priority": "MEDIUM", "text": "관심 기업 채용 공고 분석", "cta": "기업 DNA", "ctaUrl": "/dashboard/company-dna"},
            {"priority": "LOW", "text": "이력서 해당 기업 맞춤화", "cta": "이력서 매칭", "ctaUrl": "/dashboard/resume-match"},
        ],
    },
    "timeline": {
        "HEADHUNTER": [
            {"priority": "HIGH", "text": "채용 급증 구간 기업 즉시 컨택", "cta": "TOP 기업", "ctaUrl": "/dashboard/top-companies"},
            {"priority": "MEDIUM", "text": "계절적 채용 사이클 분석 후 영업 계획 수립", "cta": None, "ctaUrl": None},
            {"priority": "LOW", "text": "트렌드 기반 후보자 파이프라인 준비", "cta": "트렌드", "ctaUrl": "/dashboard/trends"},
        ],
        "INHOUSE_HR": [
            {"priority": "HIGH", "text": "채용 성수기 사전 파이프라인 구축", "cta": None, "ctaUrl": None},
            {"priority": "MEDIUM", "text": "경쟁사 채용 급증 시점 모니터링", "cta": "TOP 기업", "ctaUrl": "/dashboard/top-companies"},
            {"priority": "LOW", "text": "수급 매트릭스와 타임라인 연계 분석", "cta": "SD 매트릭스", "ctaUrl": "/dashboard/sd-matrix"},
        ],
        "CHRO": [
            {"priority": "HIGH", "text": "채용 사이클 기반 인력 계획 갱신", "cta": None, "ctaUrl": None},
            {"priority": "MEDIUM", "text": "계절 채용 예산 사전 확보", "cta": None, "ctaUrl": None},
            {"priority": "LOW", "text": "트렌드 데이터 기반 조직 전략 검토", "cta": "트렌드", "ctaUrl": "/dashboard/trends"},
        ],
        "JOB_SEEKER": [
            {"priority": "HIGH", "text": "채용 급증 시점에 맞춰 지원 타이밍 조정", "cta": None, "ctaUrl": None},
            {"priority": "MEDIUM", "text": "관심 기업 채용 패턴 파악", "cta": "기업 분석", "ctaUrl": "/dashboard/company-analysis"},
            {"priority": "LOW", "text": "비수기 활용 역량 강화", "cta": None, "ctaUrl": None},
        ],
    },
    "trends": {
        "HEADHUNTER": [
            {"priority": "HIGH", "text": "상승 트렌드 직군 선제적 후보자 확보", "cta": "SD 매트릭스", "ctaUrl": "/dashboard/sd-matrix"},
            {"priority": "MEDIUM", "text": "하락 직군 수임 우선순위 조정", "cta": None, "ctaUrl": None},
            {"priority": "LOW", "text": "트렌드 기반 클라이언트 컨설팅 자료 준비", "cta": None, "ctaUrl": None},
        ],
        "INHOUSE_HR": [
            {"priority": "HIGH", "text": "급성장 직군 채용 계획 선제 수립", "cta": None, "ctaUrl": None},
            {"priority": "MEDIUM", "text": "JD 키워드 트렌드 반영 업데이트", "cta": "JD 인사이트", "ctaUrl": "/dashboard/jd-insights"},
            {"priority": "LOW", "text": "채용 예산 재배분 검토", "cta": None, "ctaUrl": None},
        ],
        "CHRO": [
            {"priority": "HIGH", "text": "트렌드 기반 중장기 인력 계획 수립", "cta": None, "ctaUrl": None},
            {"priority": "MEDIUM", "text": "핵심 직군 이탈 리스크 점검", "cta": None, "ctaUrl": None},
            {"priority": "LOW", "text": "업스킬링 프로그램 연계 검토", "cta": None, "ctaUrl": None},
        ],
        "JOB_SEEKER": [
            {"priority": "HIGH", "text": "성장 중인 직군으로 커리어 전환 검토", "cta": "이력서 매칭", "ctaUrl": "/dashboard/resume-match"},
            {"priority": "MEDIUM", "text": "인기 기술 스택 학습 우선순위 설정", "cta": "JD 인사이트", "ctaUrl": "/dashboard/jd-insights"},
            {"priority": "LOW", "text": "하락 직군 대비 인접 역량 개발", "cta": None, "ctaUrl": None},
        ],
    },
    "resume-match": {
        "HEADHUNTER": [
            {"priority": "HIGH", "text": "매칭 점수 상위 후보자 즉시 추천 리스트 작성", "cta": None, "ctaUrl": None},
            {"priority": "MEDIUM", "text": "부족 키워드 보완 방향 후보자에게 피드백", "cta": None, "ctaUrl": None},
            {"priority": "LOW", "text": "후보자 프로파일 정기 업데이트", "cta": "후보자 프로파일러", "ctaUrl": "/dashboard/candidate-profiler"},
        ],
        "INHOUSE_HR": [
            {"priority": "HIGH", "text": "매칭 상위 기업 대상 JD 맞춤 지원", "cta": None, "ctaUrl": None},
            {"priority": "MEDIUM", "text": "JD 키워드 기반 면접 질문 준비", "cta": "JD 인사이트", "ctaUrl": "/dashboard/jd-insights"},
            {"priority": "LOW", "text": "추가 기업 매칭을 위한 이력서 보완", "cta": None, "ctaUrl": None},
        ],
        "CHRO": [
            {"priority": "HIGH", "text": "내부 인재 역량 매핑 및 갭 분석", "cta": None, "ctaUrl": None},
            {"priority": "MEDIUM", "text": "외부 인재풀과 내부 역량 비교", "cta": None, "ctaUrl": None},
            {"priority": "LOW", "text": "교육 프로그램 방향 설정", "cta": None, "ctaUrl": None},
        ],
        "JOB_SEEKER": [
            {"priority": "HIGH", "text": "매칭 점수 TOP 기업에 즉시 지원", "cta": "기회 알림", "ctaUrl": "/dashboard/opp-alert"},
            {"priority": "MEDIUM", "text": "부족 키워드 역량 강화 계획 수립", "cta": None, "ctaUrl": None},
            {"priority": "LOW", "text": "이력서 A/B 테스트로 매칭 점수 최적화", "cta": None, "ctaUrl": None},
        ],
    },
    "company-analysis": {
        "HEADHUNTER": [
            {"priority": "HIGH", "text": "채용 강도 높은 기업 수임 제안", "cta": "TOP 기업", "ctaUrl": "/dashboard/top-companies"},
            {"priority": "MEDIUM", "text": "기업 DNA 분석으로 차별화 후보자 발굴", "cta": "기업 DNA", "ctaUrl": "/dashboard/company-dna"},
            {"priority": "LOW", "text": "기업별 채용 사이클 파악 후 영업 타이밍 설정", "cta": "타임라인", "ctaUrl": "/dashboard/timeline"},
        ],
        "INHOUSE_HR": [
            {"priority": "HIGH", "text": "경쟁사 대비 채용 브랜딩 강화 포인트 파악", "cta": None, "ctaUrl": None},
            {"priority": "MEDIUM", "text": "경쟁사 JD 분석으로 자사 포지션 개선", "cta": "JD 인사이트", "ctaUrl": "/dashboard/jd-insights"},
            {"priority": "LOW", "text": "인재 유출 리스크 모니터링", "cta": None, "ctaUrl": None},
        ],
        "CHRO": [
            {"priority": "HIGH", "text": "경쟁사 채용 전략 대응 방안 수립", "cta": None, "ctaUrl": None},
            {"priority": "MEDIUM", "text": "기업 DNA 비교로 인재 확보 전략 차별화", "cta": "기업 DNA", "ctaUrl": "/dashboard/company-dna"},
            {"priority": "LOW", "text": "업계 급여 경쟁력 벤치마킹", "cta": None, "ctaUrl": None},
        ],
        "JOB_SEEKER": [
            {"priority": "HIGH", "text": "관심 기업 채용 기회 즉시 확인", "cta": "기회 알림", "ctaUrl": "/dashboard/opp-alert"},
            {"priority": "MEDIUM", "text": "기업 문화 및 성장성 분석 후 지원 우선순위 설정", "cta": None, "ctaUrl": None},
            {"priority": "LOW", "text": "이력서 해당 기업 맞춤화", "cta": "이력서 매칭", "ctaUrl": "/dashboard/resume-match"},
        ],
    },
    "market-signals": {
        "HEADHUNTER": [
            {"priority": "HIGH", "text": "급부상 시그널 직군 후보자 즉시 확보", "cta": "SD 매트릭스", "ctaUrl": "/dashboard/sd-matrix"},
            {"priority": "MEDIUM", "text": "시그널 기반 클라이언트 사전 컨설팅", "cta": None, "ctaUrl": None},
            {"priority": "LOW", "text": "주간 시장 시그널 리포트 발송", "cta": None, "ctaUrl": None},
        ],
        "INHOUSE_HR": [
            {"priority": "HIGH", "text": "시장 과열 세그먼트 채용 전략 긴급 검토", "cta": "SD 매트릭스", "ctaUrl": "/dashboard/sd-matrix"},
            {"priority": "MEDIUM", "text": "시그널 기반 채용 예산 사전 확보", "cta": None, "ctaUrl": None},
            {"priority": "LOW", "text": "후보자 파이프라인 선제 구축", "cta": "후보자 프로파일러", "ctaUrl": "/dashboard/candidate-profiler"},
        ],
        "CHRO": [
            {"priority": "HIGH", "text": "시장 변화 기반 인력 계획 긴급 조정", "cta": None, "ctaUrl": None},
            {"priority": "MEDIUM", "text": "리스크 세그먼트 리텐션 정책 강화", "cta": None, "ctaUrl": None},
            {"priority": "LOW", "text": "이사회 보고용 시장 인텔리전스 자료 준비", "cta": None, "ctaUrl": None},
        ],
        "JOB_SEEKER": [
            {"priority": "HIGH", "text": "기회 시그널 직군 즉시 지원 시작", "cta": "기회 알림", "ctaUrl": "/dashboard/opp-alert"},
            {"priority": "MEDIUM", "text": "성장 시그널 기업 집중 공략", "cta": "TOP 기업", "ctaUrl": "/dashboard/top-companies"},
            {"priority": "LOW", "text": "이력서 시그널 키워드 반영", "cta": "이력서 매칭", "ctaUrl": "/dashboard/resume-match"},
        ],
    },
}

# STARTER 플랜이 사용할 수 있는 view 목록
STARTER_ALLOWED_VIEWS: set[str] = {"sd-matrix", "top-companies"}

# Pro 플랜 이상 필요한 뷰에 대한 잠금 메시지
LOCKED_INSIGHT = "이 기능은 PRO 플랜 이상에서 사용할 수 있습니다. 업그레이드하여 더 많은 인사이트를 받아보세요."


def _get_sd_signal(current_data: dict | None) -> str:
    """currentData에서 sdRatio를 읽어 RED/YELLOW/GREEN 시그널 반환"""
    if not current_data:
        return "YELLOW"
    sd_ratio = current_data.get("sdRatio") or current_data.get("sd_ratio")
    if sd_ratio is None:
        return "YELLOW"
    try:
        ratio = float(sd_ratio)
    except (ValueError, TypeError):
        return "YELLOW"
    if ratio < 0.5:
        return "RED"
    if ratio < 1.0:
        return "YELLOW"
    return "GREEN"


def _get_insight_for_sd_matrix(user_category: str, current_data: dict | None) -> str:
    """SD Matrix view용 인사이트 — sdRatio 기반 시그널 × 사용자 카테고리"""
    signal = _get_sd_signal(current_data)
    category_insights = SD_MATRIX_INSIGHTS.get(signal, SD_MATRIX_INSIGHTS["YELLOW"])
    return category_insights.get(user_category, category_insights.get("INHOUSE_HR", ""))


def _get_default_insight(view: str, user_category: str) -> str:
    """view별 기본 인사이트 반환"""
    return VIEW_DEFAULT_INSIGHTS.get(view, "현재 데이터를 분석하여 최적의 전략을 수립하세요.")


class ActionPanelService:
    """Action Panel 생성 서비스 — rule-based (Claude API ready 구조)"""

    def generate(self, request: ActionPanelRequest) -> ActionPanelResponse:
        """view + context 기반 insight + actions 반환"""
        view = request.view
        user_category = request.context.user_category
        user_plan = request.context.user_plan
        current_data = request.context.current_data

        # STARTER 플랜은 sd-matrix, top-companies만 접근 가능
        if user_plan in ("STARTER", "TALENT_FREE") and view not in STARTER_ALLOWED_VIEWS:
            return ActionPanelResponse(
                insight=LOCKED_INSIGHT,
                actions=[],
                related_views=[],
                is_ai_generated=False,
                locked=True,
            )

        # Claude API stub — ANTHROPIC_API_KEY 설정 시 여기서 호출
        # result = self._generate_with_claude(view, user_category, current_data)
        # if result:
        #     return result

        return self._generate_rule_based(view, user_category, current_data)

    def _generate_rule_based(
        self,
        view: str,
        user_category: str,
        current_data: dict | None,
    ) -> ActionPanelResponse:
        """rule-based 인사이트 + actions 생성"""
        # 인사이트 결정
        if view == "sd-matrix":
            insight = _get_insight_for_sd_matrix(user_category, current_data)
        else:
            insight = _get_default_insight(view, user_category)

        if not insight:
            insight = VIEW_DEFAULT_INSIGHTS.get(view, "현재 데이터를 분석하여 최적의 전략을 수립하세요.")

        # actions 결정
        view_actions = VIEW_CATEGORY_ACTIONS.get(view, {})
        raw_actions = view_actions.get(user_category) or view_actions.get("INHOUSE_HR") or []
        actions = [
            ActionItem(
                priority=a["priority"],
                text=a["text"],
                cta=a.get("cta"),
                cta_url=a.get("ctaUrl"),
            )
            for a in raw_actions
        ]

        # related views
        related_views = VIEW_RELATED_VIEWS.get(view, [])

        return ActionPanelResponse(
            insight=insight,
            actions=actions,
            related_views=related_views,
            is_ai_generated=False,
            locked=False,
        )

    async def _generate_with_claude(
        self,
        view: str,
        user_category: str,
        current_data: dict | None,
    ) -> ActionPanelResponse | None:
        """Claude API를 사용한 인사이트 생성 stub — ANTHROPIC_API_KEY 설정 후 활성화

        구현 시 참고:
        - model: claude-haiku-3-5 (속도/비용 최적)
        - system prompt: view, user_category, current_data를 컨텍스트로 제공
        - output: insight(str) + actions(list[ActionItem]) + relatedViews(list[str]) JSON
        - fallback: 예외 발생 시 None 반환 → rule-based로 폴백
        """
        return None
