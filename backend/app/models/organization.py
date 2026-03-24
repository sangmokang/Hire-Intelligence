from sqlalchemy import String, DateTime, Integer, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime, timezone
import uuid
import enum

from app.database import Base


class OrgType(str, enum.Enum):
    SEARCH_FIRM = "SEARCH_FIRM"
    CORPORATION = "CORPORATION"
    INDIVIDUAL = "INDIVIDUAL"


class OrgPlan(str, enum.Enum):
    STARTER = "STARTER"
    PRO = "PRO"
    ENTERPRISE = "ENTERPRISE"


class OrgMemberRole(str, enum.Enum):
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    MEMBER = "MEMBER"


class Organization(Base):
    """조직 (헤드헌팅 회사, 기업 인사팀 등)"""
    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    type: Mapped[str] = mapped_column(
        SAEnum(OrgType, name="org_type"), nullable=False
    )
    plan: Mapped[str] = mapped_column(
        SAEnum(OrgPlan, name="org_plan"), default=OrgPlan.STARTER, nullable=False
    )
    billing_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    max_seats: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    active_seats: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # 조직 설정 (JSON)
    settings: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # 타임스탬프
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)


class OrganizationMember(Base):
    """조직 멤버십"""
    __tablename__ = "organization_members"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("user_profiles.id"), nullable=False)
    org_role: Mapped[str] = mapped_column(
        SAEnum(OrgMemberRole, name="org_member_role"), default=OrgMemberRole.MEMBER, nullable=False
    )
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
