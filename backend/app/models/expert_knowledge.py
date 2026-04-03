"""Expert Panel 지식 저장소 — 세션, 피드백, 학습된 지식"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    String, DateTime, Integer, Numeric, Text, ForeignKey,
    UniqueConstraint, Index, CheckConstraint, Boolean,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.database import Base


class ExpertSession(Base):
    """전문가 패널 세션 — /ask 호출 단위 기록"""
    __tablename__ = "expert_sessions"
    __table_args__ = (
        Index("ix_expert_sessions_user_id", "user_id"),
        Index("ix_expert_sessions_created_at", "created_at"),
        Index("ix_expert_sessions_user_created", "user_id", "created_at"),
        {"schema": "ops"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )
    query: Mapped[str] = mapped_column(String(2000), nullable=False)
    view: Mapped[str | None] = mapped_column(String(50), nullable=True)
    user_category: Mapped[str | None] = mapped_column(String(20), nullable=True)
    classification_axis: Mapped[str] = mapped_column(String(10), nullable=False)
    classification_specificity: Mapped[str] = mapped_column(String(10), nullable=False)
    classification_confidence: Mapped[float] = mapped_column(Numeric(3, 2), nullable=False, default=0.0)
    selected_experts: Mapped[list] = mapped_column(JSONB, nullable=False)
    routing_strategy: Mapped[str] = mapped_column(String(40), nullable=False)
    context_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    response_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_cache_hit: Mapped[bool] = mapped_column(Boolean, default=False)
    is_fallback: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    feedbacks: Mapped[list["ExpertFeedback"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )


class ExpertFeedback(Base):
    """전문가 응답에 대한 사용자 피드백"""
    __tablename__ = "expert_feedbacks"
    __table_args__ = (
        Index("ix_expert_feedbacks_session_id", "session_id"),
        Index("ix_expert_feedbacks_expert_type", "expert_type"),
        Index("ix_expert_feedbacks_user_id_created", "user_id", "created_at"),
        CheckConstraint("rating IS NULL OR (rating >= 1 AND rating <= 5)", name="ck_feedback_rating_range"),
        {"schema": "ops"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ops.expert_sessions.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    expert_type: Mapped[str] = mapped_column(String(30), nullable=False)
    feedback_type: Mapped[str] = mapped_column(String(20), nullable=False)  # HELPFUL / NOT_HELPFUL / FOLLOW_UP / COPY
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    feedback_text: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    session: Mapped["ExpertSession"] = relationship(back_populates="feedbacks")


class ExpertKnowledge(Base):
    """축적된 전문가 지식 — RLVR 학습 결과 저장"""
    __tablename__ = "expert_knowledge"
    __table_args__ = (
        Index("ix_expert_knowledge_expert_type", "expert_type"),
        Index("ix_expert_knowledge_expert_view", "expert_type", "view_context"),
        UniqueConstraint("expert_type", "pattern_type", "query_pattern_hash",
                         name="uq_expert_knowledge_expert_pattern"),
        CheckConstraint("confidence_score >= 0 AND confidence_score <= 1", name="ck_knowledge_confidence_range"),
        {"schema": "ops"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    expert_type: Mapped[str] = mapped_column(String(30), nullable=False)
    pattern_type: Mapped[str] = mapped_column(String(30), nullable=False)  # SUCCESS / CORRECTION / PREFERENCE
    query_pattern: Mapped[str] = mapped_column(String(500), nullable=False)
    query_pattern_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    learned_response: Mapped[str] = mapped_column(Text, nullable=False)
    view_context: Mapped[str | None] = mapped_column(String(50), nullable=True)
    user_category: Mapped[str | None] = mapped_column(String(20), nullable=True)
    confidence_score: Mapped[float] = mapped_column(Numeric(4, 3), nullable=False, default=0.500)
    usage_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    positive_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    negative_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
