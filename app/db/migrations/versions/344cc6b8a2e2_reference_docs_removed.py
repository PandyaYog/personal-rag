"""Remove reference_docs column from messages

Revision ID: 344cc6b8a2e2
Revises: 743d2f224eab
Create Date: 2025-06-30 14:38:10.494434
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '344cc6b8a2e2'
down_revision = '743d2f224eab'
branch_labels = None
depends_on = None

def upgrade():
    op.drop_column('messages', 'reference_docs')

def downgrade():
    op.add_column('messages', sa.Column('reference_docs', sa.JSON(), nullable=True))
