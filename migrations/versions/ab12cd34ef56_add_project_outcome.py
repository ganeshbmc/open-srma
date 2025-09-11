"""add project_outcome table

Revision ID: ab12cd34ef56
Revises: 9f2b3c1a5add
Create Date: 2025-09-10 02:30:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ab12cd34ef56'
down_revision = '9f2b3c1a5add'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'project_outcome',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('outcome_type', sa.String(length=50), nullable=False, server_default='dichotomous'),
        sa.ForeignKeyConstraint(['project_id'], ['project.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('project_outcome')

