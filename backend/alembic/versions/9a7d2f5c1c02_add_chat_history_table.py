"""add_chat_history_table

Revision ID: 9a7d2f5c1c02
Revises: f16337bc31cb
Create Date: 2026-03-21 23:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9a7d2f5c1c02'
down_revision: Union[str, Sequence[str], None] = 'f16337bc31cb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table('chat_history'):
        op.create_table(
            'chat_history',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('application_id', sa.UUID(), nullable=False),
            sa.Column('user_id', sa.UUID(), nullable=False),
            sa.Column('sender', sa.String(length=20), nullable=False),
            sa.Column('message', sa.Text(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['application_id'], ['loan_applications.id']),
            sa.ForeignKeyConstraint(['user_id'], ['users.id']),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('idx_chat_history_application_id', 'chat_history', ['application_id'], unique=False)
        op.create_index('idx_chat_history_created_at', 'chat_history', ['created_at'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table('chat_history'):
        op.drop_index('idx_chat_history_created_at', table_name='chat_history')
        op.drop_index('idx_chat_history_application_id', table_name='chat_history')
        op.drop_table('chat_history')
