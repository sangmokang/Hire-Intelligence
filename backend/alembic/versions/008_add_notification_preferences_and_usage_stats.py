"""add notification_preferences and usage_stats to user_profiles

Revision ID: 008
Revises: 007
Create Date: 2026-04-01

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade():
    # user_profiles 테이블에 알림 설정 JSONB 컬럼 추가
    op.add_column(
        'user_profiles',
        sa.Column(
            'notification_preferences',
            JSONB,
            nullable=True,
            server_default='{"weekly_report": true, "hiring_alert": true}',
        ),
    )
    # user_profiles 테이블에 사용량 통계 JSONB 컬럼 추가
    op.add_column(
        'user_profiles',
        sa.Column(
            'usage_stats',
            JSONB,
            nullable=True,
            server_default='{}',
        ),
    )


def downgrade():
    op.drop_column('user_profiles', 'usage_stats')
    op.drop_column('user_profiles', 'notification_preferences')
