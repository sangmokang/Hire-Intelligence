"""add billing_keys table

Revision ID: 010
Revises: 009
Create Date: 2026-04-02

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = '010'
down_revision = '009'
branch_labels = None
depends_on = None


def upgrade():
    # ops.billing_keys 테이블 생성 — Toss 빌링키(결제 수단) 저장
    op.create_table(
        'billing_keys',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('customer_key', sa.String(100), nullable=False),
        sa.Column('billing_key', sa.String(200), nullable=False),
        sa.Column('card_last_four', sa.String(4), nullable=False),
        sa.Column('card_company', sa.String(50), nullable=False),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        schema='ops',
    )
    op.create_index('ix_ops_billing_keys_user_id', 'billing_keys', ['user_id'], schema='ops')


def downgrade():
    op.drop_index('ix_ops_billing_keys_user_id', table_name='billing_keys', schema='ops')
    op.drop_table('billing_keys', schema='ops')
