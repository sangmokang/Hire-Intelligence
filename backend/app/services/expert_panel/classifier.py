"""2축 질문 분류기 — Task/Fact × Ambiguous/Concrete"""
import json
import logging

import anthropic

from app.config import settings
from app.schemas.expert_panel import QueryAxis, QuerySpecificity, QueryClassification
from app.services.expert_panel.registry import ExpertType, get_all_expert_names, search_experts

logger = logging.getLogger(__name__)


# Haiku 분류기 시스템 프롬프트
CLASSIFIER_SYSTEM_PROMPT = """당신은 HR 채용 인텔리전스 플랫폼의 질문 분류기입니다.
사용자의 질문을 2개 축으로 분류하세요:

축 1 - 의도:
- TASK: 사용자가 무언가를 하려는 질문 (전략 수립, 의사결정, 실행 계획)
- FACT: 사용자가 무언가를 알려는 질문 (데이터 조회, 현황 파악, 비교 분석)

축 2 - 구체성:
- CONCRETE: 특정 세그먼트/기업/기간이 명시된 질문
- AMBIGUOUS: 광범위하거나 조건이 불분명한 질문

전문가 선택 규칙:
- TASK + AMBIGUOUS: 3~4명의 다양한 도메인 전문가 (다각적 브레인스톰)
- TASK + CONCRETE: 가장 적합한 1명 (상세 실행 계획)
- FACT + AMBIGUOUS: DATA_SCIENTIST + BIZ_DATA_ANALYST 2명 (분석 리서치)
- FACT + CONCRETE: 가장 적합한 1명 (간결한 즉답)

반드시 아래 JSON 형식으로만 응답하세요:
{"axis": "TASK" | "FACT", "specificity": "CONCRETE" | "AMBIGUOUS", "confidence": 0.0~1.0, "selected_experts": ["전문가1", "전문가2"], "reasoning": "분류 근거"}"""


class QueryClassifier:
    """Claude Haiku 기반 2축 질문 분류기"""

    def __init__(self):
        # AsyncAnthropic 사용 — asyncio 이벤트 루프 차단 방지
        self._client: anthropic.AsyncAnthropic | None = None
        if settings.ANTHROPIC_API_KEY:
            self._client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    async def classify(
        self,
        query: str,
        view: str | None = None,
        user_category: str | None = None,
    ) -> QueryClassification:
        """사용자 질문을 2축 분류. API 키 미설정 또는 confidence < 0.6 시 rule-based 폴백."""
        if self._client is None:
            logger.info("ANTHROPIC_API_KEY 미설정 — rule-based 폴백 분류")
            return self._rule_based_classify(query, view)

        try:
            # Build user message with context
            user_msg = f"질문: {query}"
            if view:
                user_msg += f"\n현재 대시보드 뷰: {view}"
            if user_category:
                user_msg += f"\n사용자 카테고리: {user_category}"
            user_msg += f"\n사용 가능한 전문가: {', '.join(get_all_expert_names())}"

            # await로 비동기 호출 — 이벤트 루프 차단 방지
            response = await self._client.messages.create(
                model=settings.EXPERT_PANEL_CLASSIFIER_MODEL,
                max_tokens=500,
                system=CLASSIFIER_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_msg}],
                timeout=5.0,  # 분류는 빠르게
            )

            # Parse JSON response
            text = response.content[0].text.strip()
            # Handle potential markdown code block wrapping
            if text.startswith("```"):
                text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()

            data = json.loads(text)

            classification = QueryClassification(
                axis=QueryAxis(data["axis"]),
                specificity=QuerySpecificity(data["specificity"]),
                confidence=float(data.get("confidence", 0.8)),
                selected_experts=[ExpertType(e) for e in data.get("selected_experts", [])],
                reasoning=data.get("reasoning", ""),
            )

            # confidence < 0.6 → rule-based 폴백
            if classification.confidence < 0.6:
                logger.info(f"분류 confidence {classification.confidence} < 0.6 — rule-based 폴백")
                fallback = self._rule_based_classify(query, view)
                fallback.reasoning = f"LOW_CONFIDENCE_FALLBACK (original: {classification.reasoning})"
                return fallback

            return classification

        except Exception as e:
            logger.warning(f"Haiku 분류 실패: {e} — rule-based 폴백")
            return self._rule_based_classify(query, view)

    def _rule_based_classify(self, query: str, view: str | None = None) -> QueryClassification:
        """키워드 기반 rule-based 분류 폴백"""
        # 축 1: Task vs Fact 판별 (키워드 기반)
        task_keywords = ["어떻게", "전략", "계획", "개선", "최적화", "설계", "구축", "만들", "해야", "방법", "추천"]
        fact_keywords = ["얼마", "몇", "현재", "비교", "데이터", "통계", "현황", "추이", "분석", "조회"]

        task_score = sum(1 for kw in task_keywords if kw in query)
        fact_score = sum(1 for kw in fact_keywords if kw in query)
        axis = QueryAxis.TASK if task_score >= fact_score else QueryAxis.FACT

        # 축 2: Ambiguous vs Concrete 판별
        concrete_indicators = ["분기", "월", "주", "기업", "회사", "포지션", "연봉", "서울", "판교", "%", "명"]
        is_concrete = any(ind in query for ind in concrete_indicators) or len(query) > 100
        specificity = QuerySpecificity.CONCRETE if is_concrete else QuerySpecificity.AMBIGUOUS

        # 전문가 선택 (키워드 검색 기반)
        matched = search_experts(query)
        if not matched:
            # 폴백: CPO (제품 전략은 항상 관련)
            from app.services.expert_panel.registry import get_expert
            matched = [(ExpertType.CPO, get_expert(ExpertType.CPO))]

        # 라우팅 전략에 따른 전문가 수 조정은 router에서 처리
        selected = [m[0] for m in matched[:4]]

        return QueryClassification(
            axis=axis,
            specificity=specificity,
            confidence=0.5,  # rule-based는 항상 0.5
            selected_experts=selected,
            reasoning="RULE_BASED_FALLBACK",
        )
