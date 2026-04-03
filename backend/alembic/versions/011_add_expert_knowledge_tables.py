"""add expert knowledge tables (sessions, feedbacks, knowledge)

Revision ID: 011
Revises: 010
Create Date: 2026-04-03

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = '011'
down_revision = '010'
branch_labels = None
depends_on = None


def upgrade():
    # ops 스키마가 없을 경우 생성 (기존에 있으면 무시)
    op.execute("CREATE SCHEMA IF NOT EXISTS ops")

    # ops.expert_sessions — /ask 호출 단위 세션 기록
    op.create_table(
        'expert_sessions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('query', sa.String(2000), nullable=False),
        sa.Column('view', sa.String(50), nullable=True),
        sa.Column('user_category', sa.String(20), nullable=True),
        sa.Column('classification_axis', sa.String(10), nullable=False),
        sa.Column('classification_specificity', sa.String(10), nullable=False),
        sa.Column('classification_confidence', sa.Numeric(3, 2), nullable=False, server_default='0.00'),
        sa.Column('selected_experts', JSONB, nullable=False),
        sa.Column('routing_strategy', sa.String(40), nullable=False),
        sa.Column('context_data', JSONB, nullable=True),
        sa.Column('response_time_ms', sa.Integer(), nullable=True),
        sa.Column('is_cache_hit', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_fallback', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        schema='ops',
    )
    op.create_index('ix_expert_sessions_user_id', 'expert_sessions', ['user_id'], schema='ops')
    op.create_index('ix_expert_sessions_created_at', 'expert_sessions', ['created_at'], schema='ops')
    op.create_index('ix_expert_sessions_user_created', 'expert_sessions', ['user_id', 'created_at'], schema='ops')

    # ops.expert_feedbacks — 사용자 피드백 (세션별)
    op.create_table(
        'expert_feedbacks',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('session_id', UUID(as_uuid=True),
                  sa.ForeignKey('ops.expert_sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('expert_type', sa.String(30), nullable=False),
        sa.Column('feedback_type', sa.String(20), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=True),
        sa.Column('feedback_text', sa.String(1000), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "rating IS NULL OR (rating >= 1 AND rating <= 5)",
            name="ck_feedback_rating_range",
        ),
        schema='ops',
    )
    op.create_index('ix_expert_feedbacks_session_id', 'expert_feedbacks', ['session_id'], schema='ops')
    op.create_index('ix_expert_feedbacks_expert_type', 'expert_feedbacks', ['expert_type'], schema='ops')
    op.create_index('ix_expert_feedbacks_user_id_created', 'expert_feedbacks', ['user_id', 'created_at'], schema='ops')

    # ops.expert_knowledge — RLVR 학습 결과 누적 저장
    op.create_table(
        'expert_knowledge',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('expert_type', sa.String(30), nullable=False),
        sa.Column('pattern_type', sa.String(30), nullable=False),
        sa.Column('query_pattern', sa.String(500), nullable=False),
        sa.Column('query_pattern_hash', sa.String(64), nullable=False),
        sa.Column('learned_response', sa.Text(), nullable=False),
        sa.Column('view_context', sa.String(50), nullable=True),
        sa.Column('user_category', sa.String(20), nullable=True),
        sa.Column('confidence_score', sa.Numeric(4, 3), nullable=False, server_default='0.500'),
        sa.Column('usage_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('positive_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('negative_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint(
            'expert_type', 'pattern_type', 'query_pattern_hash',
            name='uq_expert_knowledge_expert_pattern',
        ),
        sa.CheckConstraint(
            "confidence_score >= 0 AND confidence_score <= 1",
            name="ck_knowledge_confidence_range",
        ),
        schema='ops',
    )
    op.create_index('ix_expert_knowledge_expert_type', 'expert_knowledge', ['expert_type'], schema='ops')
    op.create_index('ix_expert_knowledge_expert_view', 'expert_knowledge', ['expert_type', 'view_context'], schema='ops')


def downgrade():
    op.drop_index('ix_expert_knowledge_expert_view', table_name='expert_knowledge', schema='ops')
    op.drop_index('ix_expert_knowledge_expert_type', table_name='expert_knowledge', schema='ops')
    op.drop_table('expert_knowledge', schema='ops')

    op.drop_index('ix_expert_feedbacks_user_id_created', table_name='expert_feedbacks', schema='ops')
    op.drop_index('ix_expert_feedbacks_expert_type', table_name='expert_feedbacks', schema='ops')
    op.drop_index('ix_expert_feedbacks_session_id', table_name='expert_feedbacks', schema='ops')
    op.drop_table('expert_feedbacks', schema='ops')

    op.drop_index('ix_expert_sessions_user_created', table_name='expert_sessions', schema='ops')
    op.drop_index('ix_expert_sessions_created_at', table_name='expert_sessions', schema='ops')
    op.drop_index('ix_expert_sessions_user_id', table_name='expert_sessions', schema='ops')
    op.drop_table('expert_sessions', schema='ops')
