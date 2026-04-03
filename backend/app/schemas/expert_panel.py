"""Expert Panel API 스키마 — /ask 요청/응답 + 피드백"""
import json
from enum import Enum
from pydantic import field_validator

from app.config import settings
from app.schemas.common import CamelModel
from app.services.expert_panel.registry import ExpertType


# --- 분류 관련 Enum (서비스 레이어 의존성 역전 방지 — schemas가 소유) ---

class QueryAxis(str, Enum):
    """질문 의도 축"""
    TASK = "TASK"      # 과업: 무언가를 하려는 질문
    FACT = "FACT"      # 사실: 무언가를 알려는 질문


class QuerySpecificity(str, Enum):
    """질문 구체성 축"""
    AMBIGUOUS = "AMBIGUOUS"  # 모호한 질문
    CONCRETE = "CONCRETE"    # 구체적 질문


class QueryClassification(CamelModel):
    """2축 분류 결과"""
    axis: QueryAxis
    specificity: QuerySpecificity
    confidence: float  # 0.0 ~ 1.0
    selected_experts: list[ExpertType]
    reasoning: str  # 분류 근거 (디버깅용)


class ActionItem(CamelModel):
    """전문가 제안 액션"""
    priority: str = "MEDIUM"  # HIGH / MEDIUM / LOW
    text: str
    cta: str | None = None
    cta_url: str | None = None


class AskRequest(CamelModel):
    """Expert Panel 질문 요청"""
    query: str                              # 사용자 질문 (max 2000자)
    view: str | None = None                 # 현재 대시보드 뷰
    expert_hint: ExpertType | None = None   # 사용자가 지정한 전문가 (분류 건너뛰기)
    context_data: dict | None = None        # 현재 화면 데이터

    @field_validator("query")
    @classmethod
    def validate_query_length(cls, v: str) -> str:
        if len(v) > 2000:
            raise ValueError("질문은 2000자를 초과할 수 없습니다.")
        if len(v.strip()) == 0:
            raise ValueError("질문을 입력해주세요.")
        return v.strip()

    @field_validator("context_data")
    @classmethod
    def validate_context_size(cls, v: dict | None) -> dict | None:
        """context_data 직렬화 크기를 4KB 이하로 제한 — 프롬프트 인젝션 방지 + 비용 방지"""
        if v is None:
            return v
        serialized = json.dumps(v, ensure_ascii=False)
        max_size = settings.EXPERT_PANEL_MAX_CONTEXT_SIZE
        if len(serialized.encode("utf-8")) > max_size:
            raise ValueError(f"context_data는 {max_size}바이트를 초과할 수 없습니다.")
        return v


class ExpertResponseItem(CamelModel):
    """개별 전문가 응답"""
    expert: ExpertType
    expert_name: str                    # "CFO (재무최고책임자)"
    answer: str
    confidence: float
    suggested_actions: list[ActionItem] | None = None
    related_views: list[str] = []


class ClassificationResult(CamelModel):
    """분류 결과 (응답용 축소 모델)"""
    axis: QueryAxis
    specificity: QuerySpecificity
    confidence: float
    routing_strategy: str  # "MULTI_EXPERT_BRAINSTORM" etc.


class AskResponse(CamelModel):
    """Expert Panel 전체 응답"""
    classification: ClassificationResult
    responses: list[ExpertResponseItem]
    session_id: str                     # 피드백 연결용
    is_ai_generated: bool = True
