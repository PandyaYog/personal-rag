"""Add knowledgebase and document tables

Revision ID: 2b6fe4f6f384
Revises: 80754ef58ede
Create Date: 2025-06-28 13:48:10.988750

"""
from typing import Sequence, Union
from sqlalchemy.dialects import postgresql
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2b6fe4f6f384'
down_revision: Union[str, None] = '80754ef58ede'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.create_table(
        'knowledgebases',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('name', sa.String(), nullable=False, index=True),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('avatar', sa.String(), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('chunking_strategy', sa.JSON(), nullable=False),
        sa.Column('embedding_model', sa.String(), nullable=False, server_default='all-MiniLM-L6-v2')
    )

    op.create_table(
        'documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('name', sa.String(), nullable=False, index=True),
        sa.Column('file_path_in_minio', sa.String(), nullable=False, unique=True),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('file_extension', sa.String(), nullable=False),
        sa.Column('num_chunks', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('processing_status', sa.String(), nullable=False, server_default='PENDING'),
        sa.Column('kb_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('knowledgebases.id'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table('documents')
    op.drop_table('knowledgebases')
