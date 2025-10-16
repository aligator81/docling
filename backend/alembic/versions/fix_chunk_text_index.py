"""Fix chunk_text index size limitation

Revision ID: fix_chunk_text_index
Revises: 09f3b85b358c
Create Date: 2025-10-15 19:09:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fix_chunk_text_index'
down_revision = '09f3b85b358c'
branch_labels = None
depends_on = None


def upgrade():
    # Drop the problematic index that causes size limitation
    op.execute('DROP INDEX IF EXISTS idx_chunks_text')
    
    # Create a new index using MD5 hash for large text chunks
    op.execute('CREATE INDEX idx_chunks_text_hash ON document_chunks (md5(chunk_text))')
    
    # Create a text search index for better search performance
    op.execute('CREATE INDEX idx_chunks_text_gin ON document_chunks USING gin (to_tsvector(\'french\', chunk_text))')


def downgrade():
    # Drop the new indexes
    op.execute('DROP INDEX IF EXISTS idx_chunks_text_hash')
    op.execute('DROP INDEX IF EXISTS idx_chunks_text_gin')
    
    # Recreate the original index (with potential size limitations)
    op.execute('CREATE INDEX idx_chunks_text ON document_chunks (chunk_text)')