"""add help_text to custom_form_field

Revision ID: 9f2b3c1a5add
Revises: 42616aa35cf0
Create Date: 2025-09-10 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9f2b3c1a5add'
down_revision = '3a6f1e2b9cde'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('custom_form_field') as batch_op:
        batch_op.add_column(sa.Column('help_text', sa.Text(), nullable=True))


def downgrade():
    with op.batch_alter_table('custom_form_field') as batch_op:
        batch_op.drop_column('help_text')
