"""Initial schemas, user_profiles, organizations, organization_members"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create schemas
    op.execute('CREATE SCHEMA IF NOT EXISTS pulse')
    op.execute('CREATE SCHEMA IF NOT EXISTS ops')

    # organizations table
    op.create_table('organizations',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('type', sa.String(20), nullable=False),
        sa.Column('plan', sa.String(20), nullable=False, server_default='STARTER'),
        sa.Column('billing_email', sa.String(255)),
        sa.Column('max_seats', sa.Integer, nullable=False, server_default='5'),
        sa.Column('active_seats', sa.Integer, nullable=False, server_default='0'),
        sa.Column('settings', JSONB),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )

    # user_profiles table
    op.create_table('user_profiles',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', UUID(as_uuid=True), sa.ForeignKey('organizations.id'), nullable=True),
        sa.Column('name', sa.String(100)),
        sa.Column('phone', sa.String(20)),
        sa.Column('company', sa.String(200)),
        sa.Column('job_title', sa.String(100)),
        sa.Column('profile_image_url', sa.String(500)),
        sa.Column('role', sa.String(15), nullable=False, server_default='USER'),
        sa.Column('category', sa.String(20)),
        sa.Column('status', sa.String(20), nullable=False, server_default='ACTIVE'),
        sa.Column('auth_provider', sa.String(50)),
        sa.Column('blocked_at', sa.DateTime(timezone=True)),
        sa.Column('blocked_reason', sa.String(500)),
        sa.Column('blocked_until', sa.DateTime(timezone=True)),
        sa.Column('blocked_by', UUID(as_uuid=True)),
        sa.Column('delete_requested_at', sa.DateTime(timezone=True)),
        sa.Column('delete_scheduled_at', sa.DateTime(timezone=True)),
        sa.Column('delete_reason', sa.String(500)),
        sa.Column('last_login_at', sa.DateTime(timezone=True)),
        sa.Column('login_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )

    # organization_members table
    op.create_table('organization_members',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', UUID(as_uuid=True), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('user_profiles.id'), nullable=False),
        sa.Column('org_role', sa.String(10), nullable=False, server_default='MEMBER'),
        sa.Column('joined_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.UniqueConstraint('organization_id', 'user_id'),
    )


def downgrade():
    op.drop_table('organization_members')
    op.drop_table('user_profiles')
    op.drop_table('organizations')
    op.execute('DROP SCHEMA IF EXISTS ops CASCADE')
    op.execute('DROP SCHEMA IF EXISTS pulse CASCADE')
