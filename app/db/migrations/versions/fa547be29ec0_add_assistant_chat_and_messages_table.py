"""Add assistant, chat and messages table

Revision ID: fa547be29ec0
Revises: 7180fbf8b9a9
Create Date: 2025-06-29 20:39:55.339820
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'fa547be29ec0'
down_revision: Union[str, None] = '7180fbf8b9a9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'assistants',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('uuid_generate_v4()')),
        sa.Column('name', sa.String(), nullable=False, index=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('llm_config', postgresql.JSON(), nullable=False),
        sa.Column('embedding_config', postgresql.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now())
    )

    op.create_table(
        'chats',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('uuid_generate_v4()')),
        sa.Column('name', sa.String(), nullable=False, index=True, server_default=sa.text("'New Chat'")),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('assistant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('assistants.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now())
    )

    op.create_table(
        'messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('uuid_generate_v4()')),
        sa.Column('chat_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('chats.id'), nullable=False),
        sa.Column('role', sa.String(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('reference_docs', postgresql.JSON(), nullable=True),
        sa.Column('is_good', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )

    op.create_table(
        'assistant_knowledgebase',
        sa.Column('assistant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('assistants.id'), primary_key=True),
        sa.Column('knowledgebase_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('knowledgebases.id'), primary_key=True)
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('assistant_knowledgebase')
    op.drop_table('messages')
