"""Add RBAC models: user, project_membership, form_change_request; add Study.created_by

Revision ID: e3a1b9c7a001
Revises: bcf12345add6
Create Date: 2025-09-11 12:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e3a1b9c7a001'
down_revision = 'c1de23a4b567'
branch_labels = None
depends_on = None


def upgrade():
    # user table
    op.create_table(
        'user',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('is_admin', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email', name='uq_user_email'),
    )

    # project_membership table
    op.create_table(
        'project_membership',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['project.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'project_id', name='uq_membership_user_project'),
    )

    # form_change_request table
    op.create_table(
        'form_change_request',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('requested_by', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('action_type', sa.String(length=50), nullable=False),
        sa.Column('payload', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('reviewed_by', sa.Integer(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['project.id'], ),
        sa.ForeignKeyConstraint(['requested_by'], ['user.id'], ),
        sa.ForeignKeyConstraint(['reviewed_by'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )

    # study.created_by (use batch mode for SQLite to support FK addition)
    with op.batch_alter_table('study') as batch_op:
        batch_op.add_column(sa.Column('created_by', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_study_created_by_user', 'user', ['created_by'], ['id'])


def downgrade():
    # drop study.created_by (batch for SQLite)
    with op.batch_alter_table('study') as batch_op:
        batch_op.drop_constraint('fk_study_created_by_user', type_='foreignkey')
        batch_op.drop_column('created_by')

    # drop change requests and memberships, then users
    op.drop_table('form_change_request')
    op.drop_table('project_membership')
    op.drop_table('user')
