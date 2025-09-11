"""add study_continuous_outcome table

Revision ID: bcf12345add6
Revises: ab12cd34ef56
Create Date: 2025-09-10 02:45:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bcf12345add6'
down_revision = 'ab12cd34ef56'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'study_continuous_outcome',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('study_id', sa.Integer(), nullable=False),
        sa.Column('outcome_name', sa.String(length=200), nullable=False),
        sa.Column('mean_intervention', sa.Float(), nullable=True),
        sa.Column('sd_intervention', sa.Float(), nullable=True),
        sa.Column('n_intervention', sa.Integer(), nullable=True),
        sa.Column('mean_control', sa.Float(), nullable=True),
        sa.Column('sd_control', sa.Float(), nullable=True),
        sa.Column('n_control', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['study_id'], ['study.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('study_continuous_outcome')

