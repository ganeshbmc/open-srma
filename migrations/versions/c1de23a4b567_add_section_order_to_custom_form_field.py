"""add section_order to CustomFormField

Revision ID: c1de23a4b567
Revises: bcf12345add6
Create Date: 2025-09-11 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c1de23a4b567'
down_revision = 'bcf12345add6'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('custom_form_field', sa.Column('section_order', sa.Integer(), nullable=True))
    # Initialize section_order heuristically so existing projects have stable grouping
    # Set section_order per section based on the minimum id of that section
    op.execute(
        """
        WITH mins AS (
            SELECT section, MIN(id) AS min_id
            FROM custom_form_field
            GROUP BY section
        )
        UPDATE custom_form_field AS c
        SET section_order = (
            SELECT ROW_NUMBER() OVER (ORDER BY m.min_id)
            FROM mins m
            WHERE m.section = c.section
        )
        """
    )


def downgrade():
    op.drop_column('custom_form_field', 'section_order')

