"""ops 스키마 — 결제 수단(빌링키) 관리

빌링키는 Fernet 대칭 암호화로 저장/조회 시 암복호화됩니다.
BILLING_KEY_ENCRYPTION_KEY 환경변수 필요 (Fernet.generate_key()로 생성).
"""
import uuid

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.config import settings
from app.database import Base


def _get_fernet() -> Fernet | None:
    """암호화 키가 설정된 경우 Fernet 인스턴스 반환"""
    key = getattr(settings, "BILLING_KEY_ENCRYPTION_KEY", "")
    if not key:
        return None
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt_billing_key(plain: str) -> str:
    """빌링키 암호화 (키 미설정 시 평문 반환 — 개발 환경용)"""
    f = _get_fernet()
    if not f:
        return plain
    return f.encrypt(plain.encode()).decode()


def decrypt_billing_key(encrypted: str) -> str:
    """빌링키 복호화 (키 미설정 또는 평문인 경우 원본 반환)"""
    f = _get_fernet()
    if not f:
        return encrypted
    try:
        return f.decrypt(encrypted.encode()).decode()
    except (InvalidToken, Exception):
        # 평문으로 저장된 기존 데이터 호환
        return encrypted


class BillingKey(Base):
    """Toss Payments 빌링키 — 정기 결제 수단 저장 (암호화)"""
    __tablename__ = "billing_keys"
    __table_args__ = {"schema": "ops"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # user_profiles FK (공개 스키마) — 직접 ForeignKey 없이 user_id만 보관
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    # Toss 고객 식별자 — billingAuth 요청 시 사용
    customer_key = Column(String(100), nullable=False)
    # Toss 빌링키 — Fernet 암호화 후 저장 (최대 400자)
    billing_key = Column(String(400), nullable=False)
    # 카드 끝 4자리 (표시용)
    card_last_four = Column(String(4), nullable=False)
    # 카드사명
    card_company = Column(String(50), nullable=False)
    # 기본 결제 수단 여부
    is_default = Column(Boolean, default=False, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
