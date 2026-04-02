"""add payments table and payment_key to subscriptions

Revision ID: 009
Revises: 008
Create Date: 2026-04-01

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = '009'
down_revision = '008'
branch_labels = None
depends_on = None


def upgrade():
    # ops.payments 테이블 생성 — Toss Payments 결제 내역 저장
    op.create_table(
        'payments',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('public.user_profiles.id'), nullable=False),
        sa.Column('order_id', sa.String(), nullable=False),
        sa.Column('payment_key', sa.String(), nullable=True),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('method', sa.String(50), nullable=True),
        sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('order_id', name='uq_payments_order_id'),
        schema='ops',
    )
    op.create_index('ix_ops_payments_user_id', 'payments', ['user_id'], schema='ops')

    # ops.subscriptions 에 payment_key 컬럼 추가 — 유료 플랜 결제 키 연결
    op.add_column(
        'subscriptions',
        sa.Column('payment_key', sa.String(200), nullable=True),
        schema='ops',
    )


def downgrade():
    op.drop_column('subscriptions', 'payment_key', schema='ops')
    op.drop_index('ix_ops_payments_user_id', table_name='payments', schema='ops')
    op.drop_table('payments', schema='ops')
