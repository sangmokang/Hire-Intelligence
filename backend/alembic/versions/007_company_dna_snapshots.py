"""company_dna_snapshots table

Revision ID: 007
Revises: 006
Create Date: 2026-03-30
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'company_dna_snapshots',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('company_id', UUID(as_uuid=True), sa.ForeignKey('ops.companies.id'), nullable=False),
        sa.Column('segment_id', sa.String(100), nullable=False),
        sa.Column('week', sa.String(10), nullable=False),

        # Tech DNA
        sa.Column('tech_stack_count', sa.Integer(), server_default='0'),
        sa.Column('tech_diversity_index', sa.Numeric(5, 2), server_default='0'),
        sa.Column('top_techs', JSONB, server_default='[]'),
        sa.Column('tech_diversity_score', sa.Numeric(5, 2), server_default='0'),

        # Hiring DNA
        sa.Column('total_postings', sa.Integer(), server_default='0'),
        sa.Column('growth_velocity', sa.Numeric(8, 4), nullable=True),
        sa.Column('role_level_dist', JSONB, server_default='{}'),
        sa.Column('segment_breadth', sa.Integer(), server_default='0'),
        sa.Column('hiring_intensity_score', sa.Numeric(5, 2), server_default='0'),

        # Compensation DNA
        sa.Column('salary_avg', sa.Integer(), nullable=True),
        sa.Column('salary_min', sa.Integer(), nullable=True),
        sa.Column('salary_max', sa.Integer(), nullable=True),
        sa.Column('salary_position_pct', sa.Numeric(5, 2), nullable=True),
        sa.Column('has_equity_ratio', sa.Numeric(5, 2), server_default='0'),
        sa.Column('benefits_count', sa.Integer(), server_default='0'),
        sa.Column('top_benefits', JSONB, server_default='[]'),

        # Culture Signals
        sa.Column('team_size_signals', JSONB, server_default='[]'),
        sa.Column('growth_stage', sa.String(20), nullable=True),
        sa.Column('new_position_ratio', sa.Numeric(5, 2), server_default='0'),
        sa.Column('culture_score', sa.Numeric(5, 2), server_default='0'),

        # Overall
        sa.Column('overall_dna_score', sa.Numeric(5, 2), server_default='0'),

        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),

        sa.UniqueConstraint('company_id', 'week', name='uq_dna_company_week'),
        schema='pulse',
    )

    op.create_index('ix_dna_snapshots_company', 'company_dna_snapshots', ['company_id'], schema='pulse')
    op.create_index('ix_dna_snapshots_segment_week', 'company_dna_snapshots', ['segment_id', 'week'], schema='pulse')


def downgrade():
    op.drop_index('ix_dna_snapshots_segment_week', table_name='company_dna_snapshots', schema='pulse')
    op.drop_index('ix_dna_snapshots_company', table_name='company_dna_snapshots', schema='pulse')
    op.drop_table('company_dna_snapshots', schema='pulse')
