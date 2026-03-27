from sqlalchemy import String, DateTime, Integer, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
import uuid
import enum

from app.database import Base


class UserRole(str, enum.Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    USER = "USER"


class UserCategory(str, enum.Enum):
    JOB_SEEKER = "JOB_SEEKER"
    INHOUSE_HR = "INHOUSE_HR"
    HEADHUNTER = "HEADHUNTER"
    CHRO = "CHRO"


class UserStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    BLOCKED = "BLOCKED"
    PENDING_DELETE = "PENDING_DELETE"
    DELETED = "DELETED"


class UserProfile(Base):
    """사용자 프로필 (auth.users와 1:1 매핑)"""
    __tablename__ = "user_profiles"

    # Supabase auth.users의 UUID와 동일한 PK
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)

    # 기본 정보
    name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    company: Mapped[str | None] = mapped_column(String(200), nullable=True)
    job_title: Mapped[str | None] = mapped_column(String(100), nullable=True)
    profile_image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # 구독 플랜 (STARTER / PRO / ENTERPRISE)
    plan: Mapped[str] = mapped_column(String(20), default="STARTER", server_default="STARTER", nullable=False)

    # 역할 및 카테고리
    role: Mapped[str] = mapped_column(
        SAEnum(UserRole, name="user_role"), default=UserRole.USER, nullable=False
    )
    category: Mapped[str | None] = mapped_column(
        SAEnum(UserCategory, name="user_category"), nullable=True
    )
    status: Mapped[str] = mapped_column(
        SAEnum(UserStatus, name="user_status"), default=UserStatus.ACTIVE, nullable=False
    )

    # 인증 방식
    auth_provider: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # 계정 차단 관련
    blocked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    blocked_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    blocked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    blocked_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    # 탈퇴 요청 관련
    delete_requested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delete_scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delete_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # 로그인 이력
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    login_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # 타임스탬프
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
