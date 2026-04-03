"""Expert Panel API 라우터 — /ask 엔드포인트 + 피드백 + 세션 히스토리"""
import logging
import uuid as _uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.schemas.common import ApiResponse
from app.schemas.expert_panel import AskRequest, AskResponse, ExpertResponseItem, ClassificationResult
from app.schemas.expert_feedback import FeedbackRequest, FeedbackResponse, SessionSummary
from app.services.expert_panel.service import ExpertPanelService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/expert-panel", tags=["expert-panel"])


@router.post("/ask", response_model=ApiResponse[AskResponse])
async def ask_expert(
    request: AskRequest,
    user: dict = Depends(get_current_user),
) -> ApiResponse[AskResponse]:
    """전문가에게 질문 — 2축 분류 → 자동 라우팅 → 전문가 응답"""
    service = ExpertPanelService()
    result = await service.ask(
        query=request.query,
        view=request.view,
        expert_hint=request.expert_hint,
        context_data=request.context_data,
        user=user,
    )

    # dict를 Pydantic 모델로 변환
    classification = ClassificationResult(**result["classification"])
    responses = [
        ExpertResponseItem(
            expert=r["expert"],
            expert_name=r["expert_name"],
            answer=r["answer"],
            confidence=r.get("confidence", 0.8),
            suggested_actions=r.get("suggested_actions"),
            related_views=r.get("related_views", []),
        )
        for r in result["responses"]
    ]

    ask_response = AskResponse(
        classification=classification,
        responses=responses,
        session_id=result["session_id"],
        is_ai_generated=result.get("is_ai_generated", True),
    )

    return ApiResponse(data=ask_response)


@router.post("/feedback", response_model=ApiResponse[FeedbackResponse])
async def submit_feedback(
    request: FeedbackRequest,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[FeedbackResponse]:
    """전문가 응답에 대한 피드백 제출"""
    from app.models.expert_knowledge import ExpertSession, ExpertFeedback

    # 세션 존재 여부 확인
    session = db.query(ExpertSession).filter(
        ExpertSession.id == _uuid.UUID(request.session_id)
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")

    # 본인의 세션인지 확인
    if str(session.user_id) != str(user["id"]):
        raise HTTPException(status_code=403, detail="본인의 세션에만 피드백을 남길 수 있습니다.")

    feedback = ExpertFeedback(
        session_id=session.id,
        user_id=user["id"],
        expert_type=request.expert_type,
        feedback_type=request.feedback_type,
        rating=request.rating,
        feedback_text=request.feedback_text,
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)

    return ApiResponse(data=FeedbackResponse(
        id=str(feedback.id),
        session_id=str(feedback.session_id),
        feedback_type=feedback.feedback_type,
        created_at=feedback.created_at.isoformat(),
    ))


@router.get("/sessions", response_model=ApiResponse[list[SessionSummary]])
async def get_sessions(
    limit: int = Query(20, ge=1, le=50),
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[list[SessionSummary]]:
    """내 Expert Panel 세션 히스토리 조회"""
    from app.models.expert_knowledge import ExpertSession

    # FastAPI DI로 주입된 db 세션 사용 — 수동 SessionLocal() 생성 제거
    sessions = db.query(ExpertSession).filter(
        ExpertSession.user_id == user["id"]
    ).order_by(ExpertSession.created_at.desc()).limit(limit).all()

    data = [
        SessionSummary(
            id=str(s.id),
            query=s.query,
            view=s.view,
            classification_axis=s.classification_axis,
            classification_specificity=s.classification_specificity,
            selected_experts=s.selected_experts or [],
            routing_strategy=s.routing_strategy,
            response_time_ms=s.response_time_ms,
            created_at=s.created_at.isoformat(),
        )
        for s in sessions
    ]
    return ApiResponse(data=data)
