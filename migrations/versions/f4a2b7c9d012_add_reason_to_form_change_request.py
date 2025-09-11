"""add reason to form_change_request

Revision ID: f4a2b7c9d012
Revises: e3a1b9c7a001
Create Date: 2025-09-11 14:10:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f4a2b7c9d012'
down_revision = 'e3a1b9c7a001'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('form_change_request') as batch_op:
        batch_op.add_column(sa.Column('reason', sa.Text(), nullable=True))


def downgrade():
    with op.batch_alter_table('form_change_request') as batch_op:
        batch_op.drop_column('reason')

