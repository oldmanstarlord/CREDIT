"""add_ml_scoring_result_cache

Revision ID: c2d4a7f3e991
Revises: 9a7d2f5c1c02
Create Date: 2026-03-22 00:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'c2d4a7f3e991'
down_revision: Union[str, Sequence[str], None] = '9a7d2f5c1c02'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {c['name'] for c in inspector.get_columns('loan_applications')}

    if 'ml_scoring_result' not in columns:
        op.add_column(
            'loan_applications',
            sa.Column('ml_scoring_result', postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default=sa.text("'{}'::jsonb")),
        )


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {c['name'] for c in inspector.get_columns('loan_applications')}

    if 'ml_scoring_result' in columns:
        op.drop_column('loan_applications', 'ml_scoring_result')
