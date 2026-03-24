"""pulse schema tables"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    # pulse.weekly_snapshots
    op.create_table('weekly_snapshots',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('segment_id', sa.String(100), nullable=False),
        sa.Column('week', sa.String(10), nullable=False),
        sa.Column('demand', sa.Integer, nullable=False, server_default='0'),
        sa.Column('supply', sa.Integer, nullable=False, server_default='0'),
        sa.Column('sd_ratio', sa.Numeric(8, 4), nullable=False, server_default='1.0'),
        sa.Column('otw_pct', sa.Numeric(5, 2), nullable=False, server_default='0.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.UniqueConstraint('segment_id', 'week', name='uq_weekly_snapshots_segment_week'),
        schema='pulse',
    )
    op.create_index('ix_pulse_weekly_snapshots_segment_week', 'weekly_snapshots', ['segment_id', 'week'], schema='pulse')

    # pulse.segment_snapshots
    op.create_table('segment_snapshots',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('segment_id', sa.String(100), nullable=False),
        sa.Column('week', sa.String(10), nullable=False),
        sa.Column('demand', sa.Integer, nullable=False, server_default='0'),
        sa.Column('supply', sa.Integer, nullable=False, server_default='0'),
        sa.Column('otw_pct', sa.Numeric(5, 2), nullable=False, server_default='0.0'),
        sa.Column('sd_ratio', sa.Numeric(8, 4), nullable=False, server_default='1.0'),
        sa.Column('avg_salary', sa.Integer, nullable=True),
        sa.Column('top_companies', JSONB, nullable=True),
        sa.Column('metadata', JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.UniqueConstraint('segment_id', 'week', name='uq_segment_snapshots_segment_week'),
        schema='pulse',
    )
    op.create_index('ix_pulse_segment_snapshots_week', 'segment_snapshots', ['week'], schema='pulse')
    op.create_index('ix_pulse_segment_snapshots_segment_week', 'segment_snapshots', ['segment_id', 'week'], schema='pulse')

    # pulse.job_postings
    op.create_table('job_postings',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('company_id', UUID(as_uuid=True), nullable=False),
        sa.Column('segment_id', sa.String(100), nullable=False),
        sa.Column('platform', sa.String(50), nullable=False),
        sa.Column('week', sa.String(10), nullable=False),
        sa.Column('count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('positions', JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        schema='pulse',
    )
    op.create_index('ix_pulse_job_postings_company_week', 'job_postings', ['company_id', 'week'], schema='pulse')
    op.create_index('ix_pulse_job_postings_segment_week', 'job_postings', ['segment_id', 'week'], schema='pulse')

    # pulse.talent_pool
    op.create_table('talent_pool',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('segment_id', sa.String(100), nullable=False),
        sa.Column('week', sa.String(10), nullable=False),
        sa.Column('pool_size', sa.Integer, nullable=False, server_default='0'),
        sa.Column('otw_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('otw_pct', sa.Numeric(5, 2), nullable=False, server_default='0.0'),
        sa.Column('source', sa.String(50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.UniqueConstraint('segment_id', 'week', 'source', name='uq_talent_pool_segment_week_source'),
        schema='pulse',
    )

    # pulse.keyword_index
    op.create_table('keyword_index',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('keyword', sa.String(200), nullable=False),
        sa.Column('segment_id', sa.String(100), nullable=False),
        sa.Column('company_id', UUID(as_uuid=True), nullable=True),
        sa.Column('week', sa.String(10), nullable=False),
        sa.Column('count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        schema='pulse',
    )
    op.create_index('ix_pulse_keyword_index_keyword', 'keyword_index', ['keyword'], schema='pulse')
    op.create_index('ix_pulse_keyword_index_segment_week', 'keyword_index', ['segment_id', 'week'], schema='pulse')


def downgrade():
    op.drop_index('ix_pulse_keyword_index_segment_week', table_name='keyword_index', schema='pulse')
    op.drop_index('ix_pulse_keyword_index_keyword', table_name='keyword_index', schema='pulse')
    op.drop_table('keyword_index', schema='pulse')

    op.drop_table('talent_pool', schema='pulse')

    op.drop_index('ix_pulse_job_postings_segment_week', table_name='job_postings', schema='pulse')
    op.drop_index('ix_pulse_job_postings_company_week', table_name='job_postings', schema='pulse')
    op.drop_table('job_postings', schema='pulse')

    op.drop_index('ix_pulse_segment_snapshots_segment_week', table_name='segment_snapshots', schema='pulse')
    op.drop_index('ix_pulse_segment_snapshots_week', table_name='segment_snapshots', schema='pulse')
    op.drop_table('segment_snapshots', schema='pulse')

    op.drop_index('ix_pulse_weekly_snapshots_segment_week', table_name='weekly_snapshots', schema='pulse')
    op.drop_table('weekly_snapshots', schema='pulse')
