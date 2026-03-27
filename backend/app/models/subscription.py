from sqlalchemy import String, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
import uuid

from app.database import Base


class Subscription(Base):
    """사용자 구독 정보"""
    __tablename__ = "subscriptions"
    __table_args__ = (
        Index('ix_ops_subscriptions_user_id', 'user_id'),
        {"schema": "ops"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('public.user_profiles.id'), nullable=False)

    # 구독 플랜 (STARTER / PRO / ENTERPRISE)
    plan: Mapped[str] = mapped_column(String(20), nullable=False, default="STARTER")
    # 구독 상태 (active / cancelled / expired)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")

    # 구독 기간
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # 결제 수단
    payment_method: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # 타임스탬프
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
