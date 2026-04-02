from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base
import uuid
from datetime import datetime, timezone


class Payment(Base):
    """결제 내역 — Toss Payments 연동"""
    __tablename__ = "payments"
    __table_args__ = (
        UniqueConstraint('order_id', name='uq_payments_order_id'),
        {"schema": "ops"},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # user_profiles FK (공개 스키마)
    user_id = Column(UUID(as_uuid=True), ForeignKey("public.user_profiles.id"), nullable=False)
    # 주문 ID — 결제 요청 시 생성, 중복 방지용 unique
    order_id = Column(String, nullable=False)
    # Toss 결제 키 — confirm 후 수신
    payment_key = Column(String, nullable=True)
    # 결제 금액 (원화)
    amount = Column(Integer, nullable=False)
    # 결제 상태: pending / paid / cancelled / failed
    status = Column(String(20), nullable=False, default="pending")
    # 결제 수단 (카드, 계좌이체 등)
    method = Column(String(50), nullable=True)
    # 결제 완료 시각
    paid_at = Column(DateTime(timezone=True), nullable=True)
    # 결제 취소 시각
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
