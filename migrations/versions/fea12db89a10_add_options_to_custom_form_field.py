"""add options column to custom_form_field

Revision ID: fea12db89a10
Revises: f4a2b7c9d012
Create Date: 2025-09-11 15:05:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fea12db89a10'
down_revision = 'f4a2b7c9d012'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('custom_form_field') as batch_op:
        batch_op.add_column(sa.Column('options', sa.Text(), nullable=True))


def downgrade():
    with op.batch_alter_table('custom_form_field') as batch_op:
        batch_op.drop_column('options')

