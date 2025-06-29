"""Change kb embedding_model from String to JSON

Revision ID: 7180fbf8b9a9
Revises: 2b6fe4f6f384
Create Date: 2025-06-28 20:27:10.189584
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '7180fbf8b9a9'
down_revision = '2b6fe4f6f384'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('knowledgebases', sa.Column('embedding_model_tmp', postgresql.JSON(), nullable=False, server_default='{}'))
    op.execute("""
        UPDATE knowledgebases
        SET embedding_model_tmp = to_jsonb(embedding_model)
    """)
    op.drop_column('knowledgebases', 'embedding_model')
    op.alter_column('knowledgebases', 'embedding_model_tmp', new_column_name='embedding_model')


def downgrade():
    op.add_column('knowledgebases', sa.Column('embedding_model_tmp', sa.String(), nullable=False, server_default="'all-MiniLM-L6-v2'"))
    op.execute("""
        UPDATE knowledgebases
        SET embedding_model_tmp = embedding_model::text
    """)
    op.drop_column('knowledgebases', 'embedding_model')
    op.alter_column('embedding_model_tmp', new_column_name='embedding_model')
