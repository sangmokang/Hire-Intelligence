"""create subscriptions table

Revision ID: 005
Revises: 004
Create Date: 2026-03-26

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'subscriptions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('public.user_profiles.id'), nullable=False),
        sa.Column('plan', sa.String(20), nullable=False, server_default='STARTER'),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('payment_method', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        schema='ops',
    )
    op.create_index('ix_ops_subscriptions_user_id', 'subscriptions', ['user_id'], schema='ops')


def downgrade():
    op.drop_index('ix_ops_subscriptions_user_id', table_name='subscriptions', schema='ops')
    op.drop_table('subscriptions', schema='ops')
