"""JD analysis tables — raw_text on positions, jd_analyses, crawl_runs

Revision ID: 006
Revises: 005
Create Date: 2026-03-29
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade():
    # 1. positions 테이블에 raw_text, updated_at 컬럼 추가
    op.add_column('positions', sa.Column('raw_text', sa.Text(), nullable=True), schema='ops')
    op.add_column('positions', sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True), schema='ops')

    # 2. jd_analyses 테이블 생성 (pulse 스키마)
    op.create_table(
        'jd_analyses',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('position_id', UUID(as_uuid=True), sa.ForeignKey('ops.positions.id'), nullable=True),
        sa.Column('company_id', UUID(as_uuid=True), sa.ForeignKey('ops.companies.id'), nullable=True),
        sa.Column('raw_text', sa.Text(), nullable=True),  # position과 연결 불가한 예외 케이스용
        sa.Column('segment_id', sa.String(100), nullable=False),
        sa.Column('platform', sa.String(50), nullable=False),
        sa.Column('week', sa.String(10), nullable=False),
        sa.Column('parsed_data', JSONB, nullable=True),
        sa.Column('tech_stacks', JSONB, nullable=True),
        sa.Column('experience_min', sa.Integer(), nullable=True),
        sa.Column('experience_max', sa.Integer(), nullable=True),
        sa.Column('salary_min', sa.Integer(), nullable=True),
        sa.Column('salary_max', sa.Integer(), nullable=True),
        sa.Column('role_level', sa.String(20), nullable=True),
        sa.Column('domain_tags', JSONB, nullable=True),
        sa.Column('model_used', sa.String(50), nullable=True),
        sa.Column('parsed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema='pulse',
    )
    # jd_analyses 인덱스
    op.create_index('ix_jd_analyses_segment_week', 'jd_analyses', ['segment_id', 'week'], schema='pulse')
    op.create_index('ix_jd_analyses_company_id', 'jd_analyses', ['company_id'], schema='pulse')
    op.create_index('ix_jd_analyses_platform_week', 'jd_analyses', ['platform', 'week'], schema='pulse')
    op.create_index('ix_jd_analyses_tech_stacks', 'jd_analyses', ['tech_stacks'], schema='pulse', postgresql_using='gin')
    op.create_index('ix_jd_analyses_parsed_data', 'jd_analyses', ['parsed_data'], schema='pulse', postgresql_using='gin')

    # 3. crawl_runs 테이블 생성 (pulse 스키마)
    op.create_table(
        'crawl_runs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('platform', sa.String(50), nullable=False),
        sa.Column('segment_id', sa.String(100), nullable=True),
        sa.Column('total_fetched', sa.Integer(), server_default='0'),
        sa.Column('total_parsed', sa.Integer(), server_default='0'),
        sa.Column('total_errors', sa.Integer(), server_default='0'),
        sa.Column('error_log', JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema='pulse',
    )
    op.create_index('ix_crawl_runs_status', 'crawl_runs', ['status'], schema='pulse')


def downgrade():
    op.drop_table('crawl_runs', schema='pulse')
    op.drop_index('ix_jd_analyses_parsed_data', table_name='jd_analyses', schema='pulse')
    op.drop_index('ix_jd_analyses_tech_stacks', table_name='jd_analyses', schema='pulse')
    op.drop_index('ix_jd_analyses_platform_week', table_name='jd_analyses', schema='pulse')
    op.drop_index('ix_jd_analyses_company_id', table_name='jd_analyses', schema='pulse')
    op.drop_index('ix_jd_analyses_segment_week', table_name='jd_analyses', schema='pulse')
    op.drop_table('jd_analyses', schema='pulse')
    op.drop_column('positions', 'updated_at', schema='ops')
    op.drop_column('positions', 'raw_text', schema='ops')
