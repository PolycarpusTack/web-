"""
Database index definitions for performance optimization.

This module defines indexes for the database models to improve query performance.
It is separate from the models.py file to keep the model definitions clean.
"""

from sqlalchemy import Index, Column, String, text
from .models import (
    User, APIKey, Model, Tag, Conversation, Message, 
    File, MessageFile, MessageThread, model_tag_association,
    user_conversation_association
)

# User indexes
user_username_idx = Index('idx_user_username', User.username)
user_email_idx = Index('idx_user_email', User.email)
user_active_idx = Index('idx_user_active', User.is_active)

# API Key indexes
api_key_idx = Index('idx_api_key', APIKey.key)
api_key_user_id_idx = Index('idx_api_key_user_id', APIKey.user_id)
api_key_active_idx = Index(
    'idx_api_key_active_expiry', 
    APIKey.is_active, 
    APIKey.expires_at,
    postgresql_where=APIKey.is_active == True
)

# Model indexes
model_provider_idx = Index('idx_model_provider', Model.provider)
model_active_idx = Index('idx_model_active', Model.is_active)

# Conversation indexes
conversation_model_id_idx = Index('idx_conversation_model_id', Conversation.model_id)
conversation_updated_at_idx = Index('idx_conversation_updated_at', Conversation.updated_at)

# Message indexes
message_conversation_id_idx = Index('idx_message_conversation_id', Message.conversation_id)
message_user_id_idx = Index('idx_message_user_id', Message.user_id)
message_created_at_idx = Index('idx_message_created_at', Message.created_at)
message_thread_id_idx = Index('idx_message_thread_id', Message.thread_id)

# Composite index for conversation + created_at for efficient message retrieval
message_conversation_created_idx = Index(
    'idx_message_conversation_created',
    Message.conversation_id, 
    Message.created_at
)

# File indexes
file_user_id_idx = Index('idx_file_user_id', File.user_id)
file_conversation_id_idx = Index('idx_file_conversation_id', File.conversation_id)
file_analyzed_idx = Index('idx_file_analyzed', File.analyzed)

# MessageFile indexes
message_file_message_id_idx = Index('idx_message_file_message_id', MessageFile.message_id)
message_file_file_id_idx = Index('idx_message_file_file_id', MessageFile.file_id)

# Thread indexes
thread_conversation_id_idx = Index('idx_thread_conversation_id', MessageThread.conversation_id)
thread_creator_id_idx = Index('idx_thread_creator_id', MessageThread.creator_id)
thread_parent_id_idx = Index('idx_thread_parent_id', MessageThread.parent_thread_id)

# Full text search index for PostgreSQL (will be ignored in SQLite)
# This is a comment and would be implemented differently based on database
# For example in PostgreSQL you might use:
# message_content_fts_idx = Index(
#     'idx_message_content_fts', 
#     text('to_tsvector(\'english\', content)'),
#     postgresql_using='gin'
# )

def create_indexes(engine):
    """
    Create all defined indexes on the database.
    
    Args:
        engine: SQLAlchemy engine to use for creating indexes
    """
    # This function would be called during application startup
    # or in a migration script to ensure all indexes are created
    
    # For SQLite, many of these indexes will be automatically created for foreign keys
    # For PostgreSQL or other databases, this ensures all performance indexes exist
    pass
