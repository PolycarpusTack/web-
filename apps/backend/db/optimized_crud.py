"""
Optimized CRUD operations for database access.

This module provides optimized database operations for common queries,
addressing the N+1 query problem and implementing efficient pagination.
"""

from sqlalchemy import select, func, update, delete, and_, or_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
from typing import List, Dict, Any, Optional, Tuple, Union
import logging

from .models import (
    User, APIKey, Model, Tag, Conversation, Message, 
    File, MessageFile, MessageThread, user_conversation_association
)

logger = logging.getLogger(__name__)

# --- User Operations ---

async def get_users(
    db: AsyncSession, 
    skip: int = 0, 
    limit: int = 100,
    filters: Optional[Dict[str, Any]] = None
) -> List[User]:
    """
    Get users with optimized query and pagination.
    
    Args:
        db: Database session
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        filters: Dictionary of filter conditions
        
    Returns:
        List of User objects
    """
    query = select(User)
    
    # Apply filters if provided
    if filters:
        conditions = []
        if 'username' in filters:
            conditions.append(User.username.ilike(f"%{filters['username']}%"))
        if 'email' in filters:
            conditions.append(User.email.ilike(f"%{filters['email']}%"))
        if 'is_active' in filters:
            conditions.append(User.is_active == filters['is_active'])
        if 'role' in filters:
            conditions.append(User.role == filters['role'])
            
        if conditions:
            query = query.where(and_(*conditions))
    
    # Add pagination
    query = query.offset(skip).limit(limit)
    
    # Execute query
    result = await db.execute(query)
    return result.scalars().all()

async def count_users(
    db: AsyncSession,
    filters: Optional[Dict[str, Any]] = None
) -> int:
    """
    Count users with the same filters as get_users.
    Used for pagination metadata.
    
    Args:
        db: Database session
        filters: Dictionary of filter conditions
        
    Returns:
        Total count of users matching the filters
    """
    query = select(func.count()).select_from(User)
    
    # Apply filters if provided
    if filters:
        conditions = []
        if 'username' in filters:
            conditions.append(User.username.ilike(f"%{filters['username']}%"))
        if 'email' in filters:
            conditions.append(User.email.ilike(f"%{filters['email']}%"))
        if 'is_active' in filters:
            conditions.append(User.is_active == filters['is_active'])
        if 'role' in filters:
            conditions.append(User.role == filters['role'])
            
        if conditions:
            query = query.where(and_(*conditions))
    
    # Execute query
    result = await db.execute(query)
    return result.scalar()

# --- Conversation Operations ---

async def get_conversations(
    db: AsyncSession, 
    skip: int = 0, 
    limit: int = 20,
    filters: Optional[Dict[str, Any]] = None,
    include_messages: bool = False,
    include_threads: bool = False
) -> List[Conversation]:
    """
    Get conversations with optimized query, eager loading, and pagination.
    
    Args:
        db: Database session
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        filters: Dictionary of filter conditions
        include_messages: Whether to include messages with conversations
        include_threads: Whether to include threads with conversations
        
    Returns:
        List of Conversation objects with optional related data
    """
    # Start with base query
    query = select(Conversation)
    
    # Add eager loading options based on flags
    if include_messages and include_threads:
        query = query.options(
            selectinload(Conversation.messages),
            selectinload(Conversation.threads).selectinload(MessageThread.messages)
        )
    elif include_messages:
        query = query.options(selectinload(Conversation.messages))
    elif include_threads:
        query = query.options(selectinload(Conversation.threads))
    
    # User relationship is always needed
    query = query.options(selectinload(Conversation.users))
    
    # Apply filters if provided
    if filters:
        conditions = []
        if 'model_id' in filters:
            conditions.append(Conversation.model_id == filters['model_id'])
        if 'user_id' in filters:
            # This is a many-to-many relationship, need to join
            query = query.join(user_conversation_association).where(
                user_conversation_association.c.user_id == filters['user_id']
            )
        if 'title' in filters:
            conditions.append(Conversation.title.ilike(f"%{filters['title']}%"))
            
        if conditions:
            query = query.where(and_(*conditions))
    
    # Add sorting and pagination
    query = query.order_by(desc(Conversation.updated_at)).offset(skip).limit(limit)
    
    # Execute query
    result = await db.execute(query)
    return result.scalars().all()

async def get_user_conversations(
    db: AsyncSession, 
    user_id: str,
    model_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    include_message_count: bool = True
) -> List[Conversation]:
    """
    Get conversations for a specific user with optimized query.
    
    Args:
        db: Database session
        user_id: ID of the user to get conversations for
        model_id: Optional model ID to filter by
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        include_message_count: Whether to include message count with conversations
        
    Returns:
        List of Conversation objects
    """
    # Build the query with join to user_conversation_association
    query = (
        select(Conversation)
        .join(user_conversation_association)
        .where(user_conversation_association.c.user_id == user_id)
    )
    
    # Add model filter if provided
    if model_id:
        query = query.where(Conversation.model_id == model_id)
    
    # Add message count subquery if requested
    if include_message_count:
        # This approach uses a correlated subquery to count messages
        message_count = (
            select(func.count())
            .select_from(Message)
            .where(Message.conversation_id == Conversation.id)
            .scalar_subquery()
            .label("message_count")
        )
        
        query = select(Conversation, message_count).join(
            user_conversation_association
        ).where(
            user_conversation_association.c.user_id == user_id
        )
        
        if model_id:
            query = query.where(Conversation.model_id == model_id)
        
        # Add sorting and pagination
        query = query.order_by(desc(Conversation.updated_at)).offset(skip).limit(limit)
        
        # Execute query
        result = await db.execute(query)
        
        # Process results to add message_count as an attribute
        conversations = []
        for row in result:
            conversation = row[0]
            conversation.message_count = row[1]
            conversations.append(conversation)
            
        return conversations
    else:
        # Simple query without message count
        query = query.order_by(desc(Conversation.updated_at)).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

async def get_conversation_with_messages(
    db: AsyncSession,
    conversation_id: str,
    message_skip: int = 0,
    message_limit: int = 50
) -> Optional[Conversation]:
    """
    Get a conversation with its messages, optimized for pagination.
    
    Args:
        db: Database session
        conversation_id: ID of the conversation to get
        message_skip: Number of messages to skip (for pagination)
        message_limit: Maximum number of messages to return
        
    Returns:
        Conversation object with messages or None if not found
    """
    # Get the conversation
    conversation_query = (
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .options(
            selectinload(Conversation.users),
            selectinload(Conversation.model)
        )
    )
    
    conversation_result = await db.execute(conversation_query)
    conversation = conversation_result.scalar_one_or_none()
    
    if not conversation:
        return None
    
    # Get messages with pagination
    messages_query = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(asc(Message.created_at))
        .offset(message_skip)
        .limit(message_limit)
        .options(selectinload(Message.files).selectinload(MessageFile.file))
    )
    
    messages_result = await db.execute(messages_query)
    messages = messages_result.scalars().all()
    
    # Set messages on the conversation
    conversation.messages = messages
    
    # Get threads if any
    threads_query = (
        select(MessageThread)
        .where(MessageThread.conversation_id == conversation_id)
        .options(selectinload(MessageThread.messages))
    )
    
    threads_result = await db.execute(threads_query)
    threads = threads_result.scalars().all()
    
    # Set threads on the conversation
    conversation.threads = threads
    
    return conversation

# --- Message Operations ---

async def get_conversation_messages(
    db: AsyncSession,
    conversation_id: str,
    skip: int = 0,
    limit: int = 50,
    thread_id: Optional[str] = None,
    include_files: bool = True
) -> List[Message]:
    """
    Get messages for a conversation with optimized query and pagination.
    
    Args:
        db: Database session
        conversation_id: ID of the conversation to get messages for
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        thread_id: Optional thread ID to filter by
        include_files: Whether to include file attachments
        
    Returns:
        List of Message objects with optional file data
    """
    # Build query with thread filter if provided
    query = select(Message).where(Message.conversation_id == conversation_id)
    
    if thread_id:
        query = query.where(Message.thread_id == thread_id)
    else:
        # When not filtering by thread, only get root messages
        query = query.where(Message.thread_id == None)
    
    # Add eager loading for files if requested
    if include_files:
        query = query.options(
            selectinload(Message.files).selectinload(MessageFile.file)
        )
    
    # Add eager loading for user
    query = query.options(selectinload(Message.user))
    
    # Add sorting and pagination
    query = query.order_by(asc(Message.created_at)).offset(skip).limit(limit)
    
    # Execute query
    result = await db.execute(query)
    return result.scalars().all()

# --- Thread Operations ---

async def get_thread_with_messages(
    db: AsyncSession,
    thread_id: str,
    skip: int = 0,
    limit: int = 50,
    include_files: bool = True
) -> Optional[MessageThread]:
    """
    Get a thread with its messages, optimized for pagination.
    
    Args:
        db: Database session
        thread_id: ID of the thread to get
        skip: Number of messages to skip (for pagination)
        limit: Maximum number of messages to return
        include_files: Whether to include file attachments
        
    Returns:
        MessageThread object with messages or None if not found
    """
    # Get the thread
    thread_query = (
        select(MessageThread)
        .where(MessageThread.id == thread_id)
        .options(
            selectinload(MessageThread.conversation),
            selectinload(MessageThread.creator)
        )
    )
    
    thread_result = await db.execute(thread_query)
    thread = thread_result.scalar_one_or_none()
    
    if not thread:
        return None
    
    # Get messages with pagination
    messages_query = (
        select(Message)
        .where(Message.thread_id == thread_id)
        .order_by(asc(Message.created_at))
        .offset(skip)
        .limit(limit)
    )
    
    # Add eager loading for files if requested
    if include_files:
        messages_query = messages_query.options(
            selectinload(Message.files).selectinload(MessageFile.file)
        )
    
    # Add eager loading for user
    messages_query = messages_query.options(selectinload(Message.user))
    
    messages_result = await db.execute(messages_query)
    messages = messages_result.scalars().all()
    
    # Set messages on the thread
    thread.messages = messages
    
    return thread

# --- File Operations ---

async def get_conversation_files(
    db: AsyncSession,
    conversation_id: str,
    skip: int = 0,
    limit: int = 20,
    include_analysis: bool = False
) -> List[File]:
    """
    Get files for a conversation with optimized query and pagination.
    
    Args:
        db: Database session
        conversation_id: ID of the conversation to get files for
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        include_analysis: Whether to include analysis results
        
    Returns:
        List of File objects
    """
    # Build query
    query = (
        select(File)
        .where(File.conversation_id == conversation_id)
        .order_by(desc(File.created_at))
        .offset(skip)
        .limit(limit)
    )
    
    # If analysis results are large, consider excluding them from the main query
    # and loading them separately only when needed
    if not include_analysis:
        query = query.with_only_columns(
            File.id,
            File.filename,
            File.original_filename,
            File.content_type,
            File.size,
            File.created_at,
            File.user_id,
            File.conversation_id,
            File.is_public,
            File.analyzed
        )
    
    # Execute query
    result = await db.execute(query)
    return result.scalars().all()

# --- Model Operations ---

async def get_models(
    db: AsyncSession,
    filters: Optional[Dict[str, Any]] = None,
    skip: int = 0,
    limit: int = 100
) -> List[Model]:
    """
    Get models with optimized query and pagination.
    
    Args:
        db: Database session
        filters: Dictionary of filter conditions
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        
    Returns:
        List of Model objects
    """
    # Build query
    query = select(Model)
    
    # Apply filters
    if filters:
        conditions = []
        if 'provider' in filters:
            conditions.append(Model.provider == filters['provider'])
        if 'is_active' in filters:
            conditions.append(Model.is_active == filters['is_active'])
        if 'is_local' in filters:
            if filters['is_local']:
                conditions.append(Model.provider == 'ollama')
            else:
                conditions.append(Model.provider != 'ollama')
            
        if conditions:
            query = query.where(and_(*conditions))
    
    # Add eager loading, pagination and sorting
    query = query.options(selectinload(Model.tags))
    query = query.order_by(Model.name).offset(skip).limit(limit)
    
    # Execute query
    result = await db.execute(query)
    return result.scalars().all()