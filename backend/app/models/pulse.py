from sqlalchemy import String, DateTime, Integer, Numeric, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime, timezone
import uuid

from app.database import Base


class WeeklySnapshot(Base):
    """주간 전체 시장 스냅샷"""
    __tablename__ = "weekly_snapshots"
    __table_args__ = (
        UniqueConstraint('segment_id', 'week', name='uq_weekly_snapshots_segment_week'),
        Index('ix_weekly_snapshots_segment_week', 'segment_id', 'week'),
        {"schema": "pulse"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    segment_id: Mapped[str] = mapped_column(String(100), nullable=False)
    week: Mapped[str] = mapped_column(String(10), nullable=False)
    demand: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    supply: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sd_ratio: Mapped[float] = mapped_column(Numeric(8, 4), nullable=False, default=1.0)
    otw_pct: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class SegmentSnapshot(Base):
    """직군별 상세 스냅샷"""
    __tablename__ = "segment_snapshots"
    __table_args__ = (
        UniqueConstraint('segment_id', 'week', name='uq_segment_snapshots_segment_week'),
        Index('ix_segment_snapshots_week', 'week'),
        Index('ix_segment_snapshots_segment_week', 'segment_id', 'week'),
        {"schema": "pulse"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    segment_id: Mapped[str] = mapped_column(String(100), nullable=False)
    week: Mapped[str] = mapped_column(String(10), nullable=False)
    demand: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    supply: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    otw_pct: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0.0)
    sd_ratio: Mapped[float] = mapped_column(Numeric(8, 4), nullable=False, default=1.0)
    avg_salary: Mapped[int | None] = mapped_column(Integer, nullable=True)
    top_companies: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class JobPosting(Base):
    """채용 공고 집계"""
    __tablename__ = "job_postings"
    __table_args__ = (
        Index('ix_job_postings_company_week', 'company_id', 'week'),
        Index('ix_job_postings_segment_week', 'segment_id', 'week'),
        {"schema": "pulse"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    segment_id: Mapped[str] = mapped_column(String(100), nullable=False)
    platform: Mapped[str] = mapped_column(String(50), nullable=False)
    week: Mapped[str] = mapped_column(String(10), nullable=False)
    count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    positions: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class TalentPool(Base):
    """인재풀 집계"""
    __tablename__ = "talent_pool"
    __table_args__ = (
        UniqueConstraint('segment_id', 'week', 'source', name='uq_talent_pool_segment_week_source'),
        {"schema": "pulse"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    segment_id: Mapped[str] = mapped_column(String(100), nullable=False)
    week: Mapped[str] = mapped_column(String(10), nullable=False)
    pool_size: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    otw_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    otw_pct: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0.0)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class KeywordIndex(Base):
    """키워드 인덱스"""
    __tablename__ = "keyword_index"
    __table_args__ = (
        Index('ix_keyword_index_keyword', 'keyword'),
        Index('ix_keyword_index_segment_week', 'segment_id', 'week'),
        {"schema": "pulse"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    keyword: Mapped[str] = mapped_column(String(200), nullable=False)
    segment_id: Mapped[str] = mapped_column(String(100), nullable=False)
    company_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    week: Mapped[str] = mapped_column(String(10), nullable=False)
    count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
