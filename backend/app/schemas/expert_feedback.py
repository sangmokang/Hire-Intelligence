"""Expert Panel 피드백 스키마"""
from app.schemas.common import CamelModel


class FeedbackRequest(CamelModel):
    """피드백 제출 요청"""
    session_id: str
    expert_type: str
    feedback_type: str  # HELPFUL / NOT_HELPFUL / FOLLOW_UP / COPY
    rating: int | None = None  # 1~5 (선택)
    feedback_text: str | None = None  # 추가 코멘트 (선택)


class FeedbackResponse(CamelModel):
    """피드백 제출 응답"""
    id: str
    session_id: str
    feedback_type: str
    created_at: str


class SessionSummary(CamelModel):
    """세션 히스토리 요약"""
    id: str
    query: str
    view: str | None = None
    classification_axis: str
    classification_specificity: str
    selected_experts: list[str]
    routing_strategy: str
    response_time_ms: int | None = None
    created_at: str
