"""Add password reset token table

Revision ID: b6d7e8f90123
Revises: a5f0c1b2d3e4
Create Date: 2025-09-18 00:10:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b6d7e8f90123'
down_revision = 'a5f0c1b2d3e4'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'password_reset_token',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('token_hash', sa.String(length=128), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('used_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token_hash'),
    )
    op.create_index(
        'ix_password_reset_token_user_expires',
        'password_reset_token',
        ['user_id', 'expires_at'],
    )


def downgrade():
    op.drop_index('ix_password_reset_token_user_expires', table_name='password_reset_token')
    op.drop_table('password_reset_token')
