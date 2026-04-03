"""전문가 라우팅 매트릭스 — 분류 결과 기반 전문가 선택 전략"""
import logging
from dataclasses import dataclass

from app.schemas.expert_panel import QueryAxis, QuerySpecificity, QueryClassification
from app.services.expert_panel.registry import ExpertType, search_experts, get_expert

logger = logging.getLogger(__name__)


@dataclass
class RoutingStrategy:
    """라우팅 전략 정의"""
    name: str
    min_experts: int
    max_experts: int
    selection: str        # "diverse_domains" | "best_match" | "analyst_pair"
    response_mode: str    # "collaborative" | "detailed" | "analytical" | "concise"


# 2x2 라우팅 매트릭스
ROUTING_MATRIX: dict[tuple[QueryAxis, QuerySpecificity], RoutingStrategy] = {
    (QueryAxis.TASK, QuerySpecificity.AMBIGUOUS): RoutingStrategy(
        name="MULTI_EXPERT_BRAINSTORM",
        min_experts=3, max_experts=4,
        selection="diverse_domains",
        response_mode="collaborative",
    ),
    (QueryAxis.TASK, QuerySpecificity.CONCRETE): RoutingStrategy(
        name="SINGLE_EXPERT_EXECUTION",
        min_experts=1, max_experts=1,
        selection="best_match",
        response_mode="detailed",
    ),
    (QueryAxis.FACT, QuerySpecificity.AMBIGUOUS): RoutingStrategy(
        name="ANALYST_RESEARCH",
        min_experts=2, max_experts=2,
        selection="analyst_pair",
        response_mode="analytical",
    ),
    (QueryAxis.FACT, QuerySpecificity.CONCRETE): RoutingStrategy(
        name="EXPERT_LOOKUP",
        min_experts=1, max_experts=1,
        selection="best_match",
        response_mode="concise",
    ),
}


class ExpertRouter:
    """분류 결과 기반 전문가 라우팅"""

    def route(self, classification: QueryClassification, query: str) -> tuple[list[ExpertType], RoutingStrategy]:
        """분류 결과에 따라 전문가 목록과 라우팅 전략 반환"""
        strategy = ROUTING_MATRIX[(classification.axis, classification.specificity)]

        if strategy.selection == "analyst_pair":
            # ANALYST_RESEARCH: DATA_SCIENTIST + BIZ_DATA_ANALYST 고정
            experts = [ExpertType.DATA_SCIENTIST, ExpertType.BIZ_DATA_ANALYST]
        elif strategy.selection == "diverse_domains":
            # MULTI_EXPERT_BRAINSTORM: 분류기가 선택한 전문가 사용, 부족하면 키워드 검색 보충
            experts = list(classification.selected_experts)
            if len(experts) < strategy.min_experts:
                # 키워드 검색으로 보충
                additional = search_experts(query)
                for expert_type, _ in additional:
                    if expert_type not in experts:
                        experts.append(expert_type)
                    if len(experts) >= strategy.max_experts:
                        break
            # 최대 수 제한
            experts = experts[:strategy.max_experts]
        else:
            # best_match: 분류기 1순위 전문가 사용
            if classification.selected_experts:
                experts = [classification.selected_experts[0]]
            else:
                # 폴백: 키워드 검색 1순위
                matched = search_experts(query)
                experts = [matched[0][0]] if matched else [ExpertType.CPO]

        # 최소 전문가 수 보장
        if len(experts) < strategy.min_experts:
            fallback_experts = search_experts(query)
            for expert_type, _ in fallback_experts:
                if expert_type not in experts:
                    experts.append(expert_type)
                if len(experts) >= strategy.min_experts:
                    break

        logger.info(f"라우팅: {strategy.name} → {[e.value for e in experts]}")
        return experts, strategy
