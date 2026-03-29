from sqlalchemy import String, DateTime, Integer, Numeric, Text, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
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
    extra_metadata: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
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


class JdAnalysis(Base):
    """JD 분석 결과"""
    __tablename__ = "jd_analyses"
    __table_args__ = (
        Index('ix_jd_analyses_segment_week', 'segment_id', 'week'),
        Index('ix_jd_analyses_company_id', 'company_id'),
        Index('ix_jd_analyses_platform_week', 'platform', 'week'),
        {"schema": "pulse"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    position_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey('ops.positions.id'), nullable=True)
    company_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey('ops.companies.id'), nullable=True)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    segment_id: Mapped[str] = mapped_column(String(100), nullable=False)
    platform: Mapped[str] = mapped_column(String(50), nullable=False)
    week: Mapped[str] = mapped_column(String(10), nullable=False)
    parsed_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    tech_stacks: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    experience_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    experience_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    salary_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    salary_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    role_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    domain_tags: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    model_used: Mapped[str | None] = mapped_column(String(50), nullable=True)
    parsed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    position = relationship("Position", back_populates="jd_analyses")
    company = relationship("Company")


class CrawlRun(Base):
    """크롤 실행 기록"""
    __tablename__ = "crawl_runs"
    __table_args__ = (
        Index('ix_crawl_runs_status', 'status'),
        {"schema": "pulse"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    platform: Mapped[str] = mapped_column(String(50), nullable=False)
    segment_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    total_fetched: Mapped[int] = mapped_column(Integer, default=0)
    total_parsed: Mapped[int] = mapped_column(Integer, default=0)
    total_errors: Mapped[int] = mapped_column(Integer, default=0)
    error_log: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
