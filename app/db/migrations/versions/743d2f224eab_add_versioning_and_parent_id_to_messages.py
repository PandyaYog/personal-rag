"""Add parent_id and content field to messages

Revision ID: 743d2f224eab
Revises: fa547be29ec0
Create Date: 2025-06-30 14:32:20.248894
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '743d2f224eab'
down_revision = 'fa547be29ec0'
branch_labels = None
depends_on = None

def upgrade():
    # 1. Add `parent_id` column
    op.add_column('messages', sa.Column('parent_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        'messages_parent_id_fkey',
        'messages', 'messages',
        ['parent_id'], ['id'],
        ondelete='SET NULL'
    )

    # 2. Add `content` column (new field replacing `text`)
    op.add_column('messages', sa.Column('content', postgresql.JSONB(astext_type=sa.Text()), nullable=False))

    # 3. Drop old `text` column
    op.drop_column('messages', 'text')


def downgrade():
    # 1. Re-add `text` column
    op.add_column('messages', sa.Column('text', sa.Text(), nullable=False))

    # 2. Drop `content` column
    op.drop_column('messages', 'content')

    # 3. Drop `parent_id` column and FK
    op.drop_constraint('messages_parent_id_fkey', 'messages', type_='foreignkey')
    op.drop_column('messages', 'parent_id')
