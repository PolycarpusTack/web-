"""
Add performance indexes for database optimization.

Revision ID: 49f8a0e2c6d3
Revises: [replace_with_latest_revision_id]
Create Date: 2025-05-20 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic
revision = '49f8a0e2c6d3'
down_revision = None  # Replace with the most recent migration ID
branch_labels = None
depends_on = None


def upgrade():
    # User indexes
    op.create_index('idx_user_username', 'users', ['username'])
    op.create_index('idx_user_email', 'users', ['email'])
    op.create_index('idx_user_active', 'users', ['is_active'])
    
    # API Key indexes
    op.create_index('idx_api_key', 'api_keys', ['key'])
    op.create_index('idx_api_key_user_id', 'api_keys', ['user_id'])
    
    # Index for active API keys only
    op.execute(
        "CREATE INDEX idx_api_key_active_expiry ON api_keys (is_active, expires_at) "
        "WHERE is_active = True"
    )
    
    # Model indexes
    op.create_index('idx_model_provider', 'models', ['provider'])
    op.create_index('idx_model_active', 'models', ['is_active'])
    
    # Conversation indexes
    op.create_index('idx_conversation_model_id', 'conversations', ['model_id'])
    op.create_index('idx_conversation_updated_at', 'conversations', ['updated_at'])
    
    # Message indexes
    op.create_index('idx_message_conversation_id', 'messages', ['conversation_id'])
    op.create_index('idx_message_user_id', 'messages', ['user_id'])
    op.create_index('idx_message_created_at', 'messages', ['created_at'])
    op.create_index('idx_message_thread_id', 'messages', ['thread_id'])
    op.create_index('idx_message_conversation_created', 'messages', ['conversation_id', 'created_at'])
    
    # File indexes
    op.create_index('idx_file_user_id', 'files', ['user_id'])
    op.create_index('idx_file_conversation_id', 'files', ['conversation_id'])
    op.create_index('idx_file_analyzed', 'files', ['analyzed'])
    
    # MessageFile indexes
    op.create_index('idx_message_file_message_id', 'message_files', ['message_id'])
    op.create_index('idx_message_file_file_id', 'message_files', ['file_id'])
    
    # Thread indexes
    op.create_index('idx_thread_conversation_id', 'message_threads', ['conversation_id'])
    op.create_index('idx_thread_creator_id', 'message_threads', ['creator_id'])
    op.create_index('idx_thread_parent_id', 'message_threads', ['parent_thread_id'])
    
    # For PostgreSQL, add full-text search capability
    # This is database-specific, so we'll wrap it in a try/except
    try:
        # Only execute for PostgreSQL
        dialect = op.get_bind().dialect.name
        if dialect == 'postgresql':
            op.execute(
                "CREATE INDEX idx_message_content_fts ON messages "
                "USING gin(to_tsvector('english', content))"
            )
    except Exception:
        # Skip if not supported by the database
        pass


def downgrade():
    # User indexes
    op.drop_index('idx_user_username', table_name='users')
    op.drop_index('idx_user_email', table_name='users')
    op.drop_index('idx_user_active', table_name='users')
    
    # API Key indexes
    op.drop_index('idx_api_key', table_name='api_keys')
    op.drop_index('idx_api_key_user_id', table_name='api_keys')
    op.drop_index('idx_api_key_active_expiry', table_name='api_keys')
    
    # Model indexes
    op.drop_index('idx_model_provider', table_name='models')
    op.drop_index('idx_model_active', table_name='models')
    
    # Conversation indexes
    op.drop_index('idx_conversation_model_id', table_name='conversations')
    op.drop_index('idx_conversation_updated_at', table_name='conversations')
    
    # Message indexes
    op.drop_index('idx_message_conversation_id', table_name='messages')
    op.drop_index('idx_message_user_id', table_name='messages')
    op.drop_index('idx_message_created_at', table_name='messages')
    op.drop_index('idx_message_thread_id', table_name='messages')
    op.drop_index('idx_message_conversation_created', table_name='messages')
    
    # File indexes
    op.drop_index('idx_file_user_id', table_name='files')
    op.drop_index('idx_file_conversation_id', table_name='files')
    op.drop_index('idx_file_analyzed', table_name='files')
    
    # MessageFile indexes
    op.drop_index('idx_message_file_message_id', table_name='message_files')
    op.drop_index('idx_message_file_file_id', table_name='message_files')
    
    # Thread indexes
    op.drop_index('idx_thread_conversation_id', table_name='message_threads')
    op.drop_index('idx_thread_creator_id', table_name='message_threads')
    op.drop_index('idx_thread_parent_id', table_name='message_threads')
    
    # Only for PostgreSQL
    try:
        dialect = op.get_bind().dialect.name
        if dialect == 'postgresql':
            op.drop_index('idx_message_content_fts', table_name='messages')
    except Exception:
        pass
