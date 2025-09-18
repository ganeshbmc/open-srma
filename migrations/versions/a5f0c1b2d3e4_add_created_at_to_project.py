"""Add created_at column to project

Revision ID: a5f0c1b2d3e4
Revises: fea12db89a10
Create Date: 2025-09-18 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision = 'a5f0c1b2d3e4'
down_revision = 'fea12db89a10'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('project') as batch_op:
        batch_op.add_column(sa.Column('created_at', sa.DateTime(), nullable=True))

    conn = op.get_bind()
    now_value = datetime.utcnow()
    conn.execute(sa.text('UPDATE project SET created_at = :now WHERE created_at IS NULL'), {'now': now_value})

    with op.batch_alter_table('project') as batch_op:
        batch_op.alter_column('created_at', nullable=False)


def downgrade():
    with op.batch_alter_table('project') as batch_op:
        batch_op.drop_column('created_at')
