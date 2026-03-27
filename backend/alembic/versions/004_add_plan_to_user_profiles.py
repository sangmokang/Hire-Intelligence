"""add plan column to user_profiles

Revision ID: 004
Revises: 003
Create Date: 2026-03-26

"""
from alembic import op
import sqlalchemy as sa

revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    # user_profiles 테이블에 plan 컬럼 추가 (기본값: STARTER)
    op.add_column(
        'user_profiles',
        sa.Column('plan', sa.String(20), nullable=False, server_default='STARTER'),
    )


def downgrade():
    op.drop_column('user_profiles', 'plan')
