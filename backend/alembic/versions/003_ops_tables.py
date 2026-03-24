"""ops schema tables"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    # ops.companies
    op.create_table('companies',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('normalized_name', sa.String(200), nullable=False),
        sa.Column('aliases', JSONB, nullable=False, server_default='[]'),
        sa.Column('segment_id', sa.String(100), nullable=True),
        sa.Column('organization_id', UUID(as_uuid=True), sa.ForeignKey('organizations.id'), nullable=True),
        sa.Column('industry', sa.String(100), nullable=True),
        sa.Column('size', sa.String(20), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.UniqueConstraint('normalized_name', name='uq_ops_companies_normalized_name'),
        schema='ops',
    )
    op.create_index('ix_ops_companies_segment_id', 'companies', ['segment_id'], schema='ops')

    # ops.positions
    op.create_table('positions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('company_id', UUID(as_uuid=True), sa.ForeignKey('ops.companies.id'), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('segment_id', sa.String(100), nullable=True),
        sa.Column('week', sa.String(10), nullable=False),
        sa.Column('platform', sa.String(50), nullable=False),
        sa.Column('url', sa.Text, nullable=True),
        sa.Column('salary_min', sa.Integer, nullable=True),
        sa.Column('salary_max', sa.Integer, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        schema='ops',
    )
    op.create_index('ix_ops_positions_company_week', 'positions', ['company_id', 'week'], schema='ops')
    op.create_index('ix_ops_positions_segment_id', 'positions', ['segment_id'], schema='ops')


def downgrade():
    op.drop_index('ix_ops_positions_segment_id', table_name='positions', schema='ops')
    op.drop_index('ix_ops_positions_company_week', table_name='positions', schema='ops')
    op.drop_table('positions', schema='ops')

    op.drop_index('ix_ops_companies_segment_id', table_name='companies', schema='ops')
    op.drop_table('companies', schema='ops')
