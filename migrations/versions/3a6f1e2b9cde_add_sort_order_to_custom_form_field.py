"""Add sort_order to CustomFormField

Revision ID: 3a6f1e2b9cde
Revises: 42616aa35cf0
Create Date: 2025-09-10 01:15:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3a6f1e2b9cde'
down_revision = '42616aa35cf0'
branch_labels = None
depends_on = None


def upgrade():
    # Add the new column
    op.add_column('custom_form_field', sa.Column('sort_order', sa.Integer(), nullable=True))
    # Initialize sort_order to id for existing rows to maintain a stable order
    op.execute('UPDATE custom_form_field SET sort_order = id')


def downgrade():
    op.drop_column('custom_form_field', 'sort_order')

