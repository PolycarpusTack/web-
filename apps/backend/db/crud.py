from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete, and_, or_, func
from typing import List, Optional, Dict, Any, Union
from .models import (
    User, APIKey, Model, Tag, Conversation, 
    Message, File, MessageFile, UserSettings,
    ProviderCredential, UsageRecord, ProviderHealth,
    BudgetAlert, Role, Permission, Workspace,
    WorkspaceCredential, AuditLog
)
from datetime import datetime
import os
import uuid

# User CRUD operations
async def create_user(db: AsyncSession, username: str, email: str, hashed_password: str, full_name: Optional[str] = None) -> User:
    """Create a new user."""
    user = User(
        username=username,
        email=email,
        hashed_password=hashed_password,
        full_name=full_name
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

async def get_user(db: AsyncSession, user_id: str) -> Optional[User]:
    """Get a user by ID."""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()

async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    """Get a user by username."""
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()

async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """Get a user by email."""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()

async def update_user(db: AsyncSession, user_id: str, data: Dict[str, Any]) -> Optional[User]:
    """Update a user."""
    await db.execute(
        update(User)
        .where(User.id == user_id)
        .values(**data)
    )
    await db.commit()
    return await get_user(db, user_id)

async def delete_user(db: AsyncSession, user_id: str) -> bool:
    """Delete a user."""
    await db.execute(delete(User).where(User.id == user_id))
    await db.commit()
    return True

async def get_users(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[User]:
    """Get all users with pagination."""
    result = await db.execute(
        select(User)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

# API Key operations
async def create_api_key(db: AsyncSession, user_id: str, key: str, name: str, expires_at: Optional[datetime] = None) -> APIKey:
    """Create a new API key."""
    api_key = APIKey(
        user_id=user_id,
        key=key,
        name=name,
        expires_at=expires_at
    )
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)
    return api_key

async def get_api_key(db: AsyncSession, key: str) -> Optional[APIKey]:
    """Get an API key by its value."""
    result = await db.execute(select(APIKey).where(APIKey.key == key))
    return result.scalar_one_or_none()

async def get_api_key_by_id(db: AsyncSession, api_key_id: str) -> Optional[APIKey]:
    """Get an API key by its ID."""
    result = await db.execute(select(APIKey).where(APIKey.id == api_key_id))
    return result.scalar_one_or_none()

async def get_user_api_keys(db: AsyncSession, user_id: str) -> List[APIKey]:
    """Get all API keys for a user."""
    result = await db.execute(
        select(APIKey)
        .where(APIKey.user_id == user_id)
        .order_by(APIKey.created_at.desc())
    )
    return result.scalars().all()

async def update_api_key(db: AsyncSession, api_key_id: str, data: Dict[str, Any]) -> Optional[APIKey]:
    """Update an API key."""
    await db.execute(
        update(APIKey)
        .where(APIKey.id == api_key_id)
        .values(**data)
    )
    await db.commit()
    return await get_api_key_by_id(db, api_key_id)

async def delete_api_key(db: AsyncSession, api_key_id: str) -> bool:
    """Delete an API key."""
    await db.execute(delete(APIKey).where(APIKey.id == api_key_id))
    await db.commit()
    return True

async def validate_api_key(db: AsyncSession, key: str) -> Optional[APIKey]:
    """Validate an API key and update its last used time."""
    api_key = await get_api_key(db, key)
    if api_key and api_key.is_active:
        # Check expiration
        if api_key.expires_at and api_key.expires_at < datetime.now():
            return None
        
        # Update last used time
        api_key.last_used_at = datetime.now()
        await db.commit()
        return api_key
    return None

# Model operations
async def create_model(db: AsyncSession, model_data: Dict[str, Any]) -> Model:
    """Create a new model entry."""
    model = Model(**model_data)
    db.add(model)
    await db.commit()
    await db.refresh(model)
    return model

async def get_model(db: AsyncSession, model_id: str) -> Optional[Model]:
    """Get a model by ID."""
    result = await db.execute(select(Model).where(Model.id == model_id))
    return result.scalar_one_or_none()

async def get_models(db: AsyncSession, filters: Optional[Dict[str, Any]] = None) -> List[Model]:
    """Get all models with optional filtering."""
    query = select(Model)
    if filters:
        conditions = []
        if "provider" in filters:
            conditions.append(Model.provider == filters["provider"])
        if "is_active" in filters:
            conditions.append(Model.is_active == filters["is_active"])
        if "search" in filters:
            search_term = f"%{filters['search']}%"
            conditions.append(or_(
                Model.name.ilike(search_term),
                Model.description.ilike(search_term)
            ))
        if conditions:
            query = query.where(and_(*conditions))
    
    result = await db.execute(query)
    return result.scalars().all()

async def update_model(db: AsyncSession, model_id: str, data: Dict[str, Any]) -> Optional[Model]:
    """Update a model."""
    await db.execute(
        update(Model)
        .where(Model.id == model_id)
        .values(**data)
    )
    await db.commit()
    return await get_model(db, model_id)

async def delete_model(db: AsyncSession, model_id: str) -> bool:
    """Delete a model."""
    await db.execute(delete(Model).where(Model.id == model_id))
    await db.commit()
    return True

# Conversation and Message operations
async def create_conversation(db: AsyncSession, model_id: str, title: str, system_prompt: Optional[str] = None) -> Conversation:
    """Create a new conversation."""
    conversation = Conversation(
        model_id=model_id,
        title=title,
        system_prompt=system_prompt
    )
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)
    return conversation

async def add_user_to_conversation(db: AsyncSession, conversation_id: str, user_id: str) -> bool:
    """Add a user to a conversation."""
    conversation = await get_conversation(db, conversation_id)
    if not conversation:
        return False
    
    user = await get_user(db, user_id)
    if not user:
        return False
    
    if user not in conversation.users:
        conversation.users.append(user)
        await db.commit()
    
    return True

async def get_conversation(db: AsyncSession, conversation_id: str) -> Optional[Conversation]:
    """Get a conversation by ID."""
    result = await db.execute(select(Conversation).where(Conversation.id == conversation_id))
    return result.scalar_one_or_none()

async def get_user_conversations(db: AsyncSession, user_id: str, model_id: Optional[str] = None) -> List[Conversation]:
    """Get all conversations for a user, optionally filtered by model."""
    query = select(Conversation).join(
        Conversation.users
    ).where(User.id == user_id)
    
    if model_id:
        query = query.where(Conversation.model_id == model_id)
    
    query = query.order_by(Conversation.updated_at.desc())
    
    result = await db.execute(query)
    return result.scalars().all()

async def add_message(db: AsyncSession, conversation_id: str, role: str, content: str, user_id: Optional[str] = None, tokens: int = 0, cost: float = 0.0, metadata: Optional[Dict[str, Any]] = None) -> Message:
    """Add a message to a conversation."""
    message = Message(
        conversation_id=conversation_id,
        user_id=user_id,
        role=role,
        content=content,
        tokens=tokens,
        cost=cost,
        metadata=metadata
    )
    db.add(message)
    
    # Update conversation's updated_at timestamp
    await db.execute(
        update(Conversation)
        .where(Conversation.id == conversation_id)
        .values(updated_at=datetime.now())
    )
    
    await db.commit()
    await db.refresh(message)
    return message

async def get_conversation_messages(db: AsyncSession, conversation_id: str) -> List[Message]:
    """Get all messages for a conversation."""
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    )
    return result.scalars().all()

async def delete_message(db: AsyncSession, message_id: str) -> bool:
    """Delete a message."""
    message = await db.get(Message, message_id)
    if not message:
        return False
    
    await db.delete(message)
    await db.commit()
    return True

# File operations
async def create_file(
    db: AsyncSession, 
    filename: str, 
    original_filename: str,
    content_type: str,
    size: int,
    path: str,
    user_id: str,
    conversation_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    is_public: bool = False
) -> File:
    """Create a new file entry."""
    file = File(
        filename=filename,
        original_filename=original_filename,
        content_type=content_type,
        size=size,
        path=path,
        user_id=user_id,
        conversation_id=conversation_id,
        metadata=metadata,
        is_public=is_public
    )
    db.add(file)
    await db.commit()
    await db.refresh(file)
    return file

async def get_file(db: AsyncSession, file_id: str) -> Optional[File]:
    """Get a file by ID."""
    result = await db.execute(select(File).where(File.id == file_id))
    return result.scalar_one_or_none()

async def get_file_by_path(db: AsyncSession, path: str) -> Optional[File]:
    """Get a file by its storage path."""
    result = await db.execute(select(File).where(File.path == path))
    return result.scalar_one_or_none()

async def get_user_files(db: AsyncSession, user_id: str) -> List[File]:
    """Get all files for a user."""
    result = await db.execute(
        select(File)
        .where(File.user_id == user_id)
        .order_by(File.created_at.desc())
    )
    return result.scalars().all()

async def get_conversation_files(db: AsyncSession, conversation_id: str) -> List[File]:
    """Get all files for a conversation."""
    result = await db.execute(
        select(File)
        .where(File.conversation_id == conversation_id)
        .order_by(File.created_at.desc())
    )
    return result.scalars().all()

async def get_message_files(db: AsyncSession, message_id: str) -> List[File]:
    """Get all files attached to a message."""
    result = await db.execute(
        select(File)
        .join(MessageFile, MessageFile.file_id == File.id)
        .where(MessageFile.message_id == message_id)
    )
    return result.scalars().all()

async def update_file(db: AsyncSession, file_id: str, data: Dict[str, Any]) -> Optional[File]:
    """Update a file's metadata."""
    await db.execute(
        update(File)
        .where(File.id == file_id)
        .values(**data)
    )
    await db.commit()
    return await get_file(db, file_id)

async def delete_file(db: AsyncSession, file_id: str, delete_from_storage: bool = True) -> bool:
    """Delete a file record and optionally the file from storage."""
    file = await get_file(db, file_id)
    if not file:
        return False
    
    # Delete the file from storage if requested
    if delete_from_storage and file.path and os.path.exists(file.path):
        try:
            os.remove(file.path)
        except OSError:
            # Log error but continue with record deletion
            print(f"Error deleting file from disk: {file.path}")
    
    # Delete associations
    await db.execute(delete(MessageFile).where(MessageFile.file_id == file_id))
    
    # Delete the file record
    await db.delete(file)
    await db.commit()
    return True

async def associate_file_with_message(db: AsyncSession, file_id: str, message_id: str) -> bool:
    """Associate a file with a message."""
    # Check if the file and message exist
    file = await get_file(db, file_id)
    message = await db.get(Message, message_id)
    
    if not file or not message:
        return False
    
    # Create the association
    message_file = MessageFile(
        message_id=message_id,
        file_id=file_id
    )
    db.add(message_file)
    await db.commit()
    return True

async def remove_file_from_message(db: AsyncSession, file_id: str, message_id: str) -> bool:
    """Remove a file association from a message."""
    result = await db.execute(
        delete(MessageFile)
        .where(and_(
            MessageFile.file_id == file_id,
            MessageFile.message_id == message_id
        ))
    )
    await db.commit()
    return result.rowcount > 0

# Tag operations
async def create_tag(db: AsyncSession, name: str, description: Optional[str] = None) -> Tag:
    """Create a new tag."""
    tag = Tag(name=name, description=description)
    db.add(tag)
    await db.commit()
    await db.refresh(tag)
    return tag

async def get_tag(db: AsyncSession, tag_id: int) -> Optional[Tag]:
    """Get a tag by ID."""
    result = await db.execute(select(Tag).where(Tag.id == tag_id))
    return result.scalar_one_or_none()

async def get_tag_by_name(db: AsyncSession, name: str) -> Optional[Tag]:
    """Get a tag by name."""
    result = await db.execute(select(Tag).where(Tag.name == name))
    return result.scalar_one_or_none()

async def get_or_create_tag(db: AsyncSession, name: str) -> Tag:
    """Get a tag by name or create it if it doesn't exist."""
    tag = await get_tag_by_name(db, name)
    if not tag:
        tag = await create_tag(db, name)
    return tag

async def add_tag_to_model(db: AsyncSession, model_id: str, tag_name: str) -> bool:
    """Add a tag to a model."""
    model = await get_model(db, model_id)
    if not model:
        return False
    
    tag = await get_or_create_tag(db, tag_name)
    
    # Check if the relationship already exists
    if tag not in model.tags:
        model.tags.append(tag)
        await db.commit()
    
    return True


# User Settings CRUD operations
async def get_user_settings(db: AsyncSession, user_id: str) -> Optional[UserSettings]:
    """Get user settings by user ID."""
    result = await db.execute(select(UserSettings).where(UserSettings.user_id == user_id))
    return result.scalar_one_or_none()

async def create_user_settings(db: AsyncSession, user_id: str, settings_data: Optional[Dict[str, Any]] = None) -> UserSettings:
    """Create user settings."""
    settings = UserSettings(
        user_id=user_id,
        provider_credentials=settings_data.get("provider_credentials") if settings_data else None,
        preferences=settings_data.get("preferences") if settings_data else None,
        usage_limits=settings_data.get("usage_limits") if settings_data else None,
        notification_settings=settings_data.get("notification_settings") if settings_data else None
    )
    db.add(settings)
    await db.commit()
    await db.refresh(settings)
    return settings

async def update_user_settings(db: AsyncSession, user_id: str, data: Dict[str, Any]) -> Optional[UserSettings]:
    """Update user settings."""
    # Get existing settings or create new ones
    settings = await get_user_settings(db, user_id)
    if not settings:
        settings = await create_user_settings(db, user_id, data)
        return settings
    
    await db.execute(
        update(UserSettings)
        .where(UserSettings.user_id == user_id)
        .values(**data, updated_at=datetime.utcnow())
    )
    await db.commit()
    return await get_user_settings(db, user_id)

async def get_user_provider_credentials(db: AsyncSession, user_id: str) -> Dict[str, Any]:
    """Get provider credentials for a user."""
    settings = await get_user_settings(db, user_id)
    if settings and settings.provider_credentials:
        return settings.provider_credentials
    return {}

async def update_user_provider_credentials(db: AsyncSession, user_id: str, provider_type: str, credentials: Dict[str, Any]) -> bool:
    """Update provider credentials for a user."""
    settings = await get_user_settings(db, user_id)
    if not settings:
        settings = await create_user_settings(db, user_id)
    
    # Get existing provider credentials or create new dict
    provider_creds = settings.provider_credentials or {}
    provider_creds[provider_type] = credentials
    
    await update_user_settings(db, user_id, {"provider_credentials": provider_creds})
    return True


# Provider Credentials CRUD operations
async def create_provider_credential(
    db: AsyncSession, 
    user_id: str, 
    provider_type: str, 
    credential_name: str,
    encrypted_api_key: str,
    encrypted_data: Optional[Dict[str, Any]] = None
) -> ProviderCredential:
    """Create a provider credential."""
    credential = ProviderCredential(
        user_id=user_id,
        provider_type=provider_type,
        credential_name=credential_name,
        encrypted_api_key=encrypted_api_key,
        encrypted_data=encrypted_data
    )
    db.add(credential)
    await db.commit()
    await db.refresh(credential)
    return credential

async def get_provider_credential(db: AsyncSession, credential_id: str) -> Optional[ProviderCredential]:
    """Get a provider credential by ID."""
    result = await db.execute(select(ProviderCredential).where(ProviderCredential.id == credential_id))
    return result.scalar_one_or_none()

async def get_user_provider_credentials_detailed(db: AsyncSession, user_id: str, provider_type: Optional[str] = None) -> List[ProviderCredential]:
    """Get detailed provider credentials for a user."""
    query = select(ProviderCredential).where(ProviderCredential.user_id == user_id)
    if provider_type:
        query = query.where(ProviderCredential.provider_type == provider_type)
    
    result = await db.execute(query.order_by(ProviderCredential.created_at.desc()))
    return result.scalars().all()

async def update_provider_credential(db: AsyncSession, credential_id: str, data: Dict[str, Any]) -> Optional[ProviderCredential]:
    """Update a provider credential."""
    await db.execute(
        update(ProviderCredential)
        .where(ProviderCredential.id == credential_id)
        .values(**data, updated_at=datetime.utcnow())
    )
    await db.commit()
    return await get_provider_credential(db, credential_id)

async def delete_provider_credential(db: AsyncSession, credential_id: str, user_id: str) -> bool:
    """Delete a provider credential (with user ownership check)."""
    result = await db.execute(
        delete(ProviderCredential)
        .where(and_(
            ProviderCredential.id == credential_id,
            ProviderCredential.user_id == user_id
        ))
    )
    await db.commit()
    return result.rowcount > 0


# Usage Record CRUD operations
async def create_usage_record(
    db: AsyncSession,
    user_id: str,
    provider_type: str,
    model_id: str,
    operation: str,
    input_tokens: int = 0,
    output_tokens: int = 0,
    cost: float = 0.0,
    pipeline_id: Optional[str] = None,
    execution_id: Optional[str] = None,
    request_id: Optional[str] = None,
    response_time: Optional[float] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> UsageRecord:
    """Create a usage record."""
    usage = UsageRecord(
        user_id=user_id,
        provider_type=provider_type,
        model_id=model_id,
        operation=operation,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=input_tokens + output_tokens,
        cost=cost,
        pipeline_id=pipeline_id,
        execution_id=execution_id,
        request_id=request_id,
        response_time=response_time,
        metadata=metadata
    )
    db.add(usage)
    await db.commit()
    await db.refresh(usage)
    return usage

async def get_usage_records(
    db: AsyncSession,
    user_id: Optional[str] = None,
    provider_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100
) -> List[UsageRecord]:
    """Get usage records with filtering."""
    query = select(UsageRecord)
    
    conditions = []
    if user_id:
        conditions.append(UsageRecord.user_id == user_id)
    if provider_type:
        conditions.append(UsageRecord.provider_type == provider_type)
    if start_date:
        conditions.append(UsageRecord.created_at >= start_date)
    if end_date:
        conditions.append(UsageRecord.created_at <= end_date)
    
    if conditions:
        query = query.where(and_(*conditions))
    
    query = query.order_by(UsageRecord.created_at.desc()).offset(skip).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()

async def get_usage_summary(
    db: AsyncSession,
    user_id: str,
    provider_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> Dict[str, Any]:
    """Get usage summary statistics."""
    query = select(
        func.count(UsageRecord.id).label('total_requests'),
        func.sum(UsageRecord.total_tokens).label('total_tokens'),
        func.sum(UsageRecord.cost).label('total_cost'),
        func.avg(UsageRecord.cost).label('average_cost_per_request'),
        func.avg(UsageRecord.total_tokens).label('average_tokens_per_request')
    ).where(UsageRecord.user_id == user_id)
    
    conditions = [UsageRecord.user_id == user_id]
    if provider_type:
        conditions.append(UsageRecord.provider_type == provider_type)
    if start_date:
        conditions.append(UsageRecord.created_at >= start_date)
    if end_date:
        conditions.append(UsageRecord.created_at <= end_date)
    
    query = query.where(and_(*conditions))
    
    result = await db.execute(query)
    row = result.first()
    
    if not row:
        return {
            'total_requests': 0,
            'total_tokens': 0,
            'total_cost': 0.0,
            'average_cost_per_request': 0.0,
            'average_tokens_per_request': 0.0,
            'models_used': {},
            'operations': {}
        }
    
    # Get additional breakdowns
    models_query = select(
        UsageRecord.model_id,
        func.count(UsageRecord.id).label('count'),
        func.sum(UsageRecord.cost).label('cost')
    ).where(and_(*conditions)).group_by(UsageRecord.model_id)
    
    models_result = await db.execute(models_query)
    models_used = {row.model_id: {'count': row.count, 'cost': float(row.cost or 0)} for row in models_result}
    
    operations_query = select(
        UsageRecord.operation,
        func.count(UsageRecord.id).label('count'),
        func.sum(UsageRecord.cost).label('cost')
    ).where(and_(*conditions)).group_by(UsageRecord.operation)
    
    operations_result = await db.execute(operations_query)
    operations = {row.operation: {'count': row.count, 'cost': float(row.cost or 0)} for row in operations_result}
    
    return {
        'total_requests': row.total_requests or 0,
        'total_tokens': row.total_tokens or 0,
        'total_cost': float(row.total_cost or 0),
        'average_cost_per_request': float(row.average_cost_per_request or 0),
        'average_tokens_per_request': float(row.average_tokens_per_request or 0),
        'models_used': models_used,
        'operations': operations
    }


# Provider Health CRUD operations
async def update_provider_health(
    db: AsyncSession,
    provider_type: str,
    is_available: bool,
    response_time: Optional[float] = None,
    error_rate: Optional[float] = None,
    status_message: Optional[str] = None,
    models_count: Optional[int] = None,
    capabilities: Optional[List[str]] = None,
    pricing_data: Optional[Dict[str, Any]] = None
) -> ProviderHealth:
    """Update or create provider health record."""
    # Try to get existing record
    result = await db.execute(select(ProviderHealth).where(ProviderHealth.provider_type == provider_type))
    health = result.scalar_one_or_none()
    
    if health:
        # Update existing
        update_data = {
            'is_available': is_available,
            'last_check_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        if response_time is not None:
            update_data['response_time'] = response_time
        if error_rate is not None:
            update_data['error_rate'] = error_rate
        if status_message is not None:
            update_data['status_message'] = status_message
        if models_count is not None:
            update_data['models_count'] = models_count
        if capabilities is not None:
            update_data['capabilities'] = capabilities
        if pricing_data is not None:
            update_data['pricing_data'] = pricing_data
        
        await db.execute(
            update(ProviderHealth)
            .where(ProviderHealth.provider_type == provider_type)
            .values(**update_data)
        )
        await db.commit()
        
        # Get updated record
        result = await db.execute(select(ProviderHealth).where(ProviderHealth.provider_type == provider_type))
        return result.scalar_one()
    else:
        # Create new
        health = ProviderHealth(
            provider_type=provider_type,
            is_available=is_available,
            response_time=response_time,
            error_rate=error_rate or 0.0,
            status_message=status_message,
            models_count=models_count or 0,
            capabilities=capabilities,
            pricing_data=pricing_data
        )
        db.add(health)
        await db.commit()
        await db.refresh(health)
        return health

async def get_provider_health(db: AsyncSession, provider_type: str) -> Optional[ProviderHealth]:
    """Get provider health by type."""
    result = await db.execute(select(ProviderHealth).where(ProviderHealth.provider_type == provider_type))
    return result.scalar_one_or_none()

async def get_all_provider_health(db: AsyncSession) -> List[ProviderHealth]:
    """Get all provider health records."""
    result = await db.execute(select(ProviderHealth).order_by(ProviderHealth.provider_type))
    return result.scalars().all()


# Budget Alert CRUD operations  
async def create_budget_alert(
    db: AsyncSession,
    user_id: str,
    alert_name: str,
    threshold_amount: float,
    period: str,
    provider_type: Optional[str] = None
) -> BudgetAlert:
    """Create a budget alert."""
    alert = BudgetAlert(
        user_id=user_id,
        alert_name=alert_name,
        threshold_amount=threshold_amount,
        period=period,
        provider_type=provider_type
    )
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    return alert

async def get_user_budget_alerts(db: AsyncSession, user_id: str) -> List[BudgetAlert]:
    """Get all budget alerts for a user."""
    result = await db.execute(
        select(BudgetAlert)
        .where(BudgetAlert.user_id == user_id)
        .order_by(BudgetAlert.created_at.desc())
    )
    return result.scalars().all()

async def update_budget_alert(db: AsyncSession, alert_id: str, data: Dict[str, Any]) -> Optional[BudgetAlert]:
    """Update a budget alert."""
    await db.execute(
        update(BudgetAlert)
        .where(BudgetAlert.id == alert_id)
        .values(**data, updated_at=datetime.utcnow())
    )
    await db.commit()
    
    result = await db.execute(select(BudgetAlert).where(BudgetAlert.id == alert_id))
    return result.scalar_one_or_none()

async def delete_budget_alert(db: AsyncSession, alert_id: str, user_id: str) -> bool:
    """Delete a budget alert (with user ownership check)."""
    result = await db.execute(
        delete(BudgetAlert)
        .where(and_(
            BudgetAlert.id == alert_id,
            BudgetAlert.user_id == user_id
        ))
    )
    await db.commit()
    return result.rowcount > 0


# ==================== RBAC CRUD OPERATIONS ====================

# Role CRUD operations
async def create_role(
    db: AsyncSession,
    name: str,
    display_name: str,
    description: Optional[str] = None,
    is_system: bool = False,
    parent_role_id: Optional[str] = None,
    created_by: Optional[str] = None
) -> Role:
    """Create a new role."""
    # Calculate level based on parent
    level = 0
    if parent_role_id:
        parent = await get_role(db, parent_role_id)
        if parent:
            level = parent.level + 1
    
    role = Role(
        name=name,
        display_name=display_name,
        description=description,
        is_system=is_system,
        parent_role_id=parent_role_id,
        level=level,
        created_by=created_by
    )
    db.add(role)
    await db.commit()
    await db.refresh(role)
    return role

async def get_role(db: AsyncSession, role_id: str) -> Optional[Role]:
    """Get a role by ID."""
    result = await db.execute(select(Role).where(Role.id == role_id))
    return result.scalar_one_or_none()

async def get_role_by_name(db: AsyncSession, name: str) -> Optional[Role]:
    """Get a role by name."""
    result = await db.execute(select(Role).where(Role.name == name))
    return result.scalar_one_or_none()

async def get_roles(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Role]:
    """Get all roles with pagination."""
    result = await db.execute(
        select(Role)
        .where(Role.is_active == True)
        .order_by(Role.level, Role.name)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

async def update_role(db: AsyncSession, role_id: str, data: Dict[str, Any]) -> Optional[Role]:
    """Update a role."""
    await db.execute(
        update(Role)
        .where(Role.id == role_id)
        .values(**data, updated_at=datetime.utcnow())
    )
    await db.commit()
    return await get_role(db, role_id)

async def delete_role(db: AsyncSession, role_id: str) -> bool:
    """Delete a role (only if not system role)."""
    # Check if it's a system role
    role = await get_role(db, role_id)
    if role and role.is_system:
        return False
    
    await db.execute(delete(Role).where(Role.id == role_id))
    await db.commit()
    return True

async def assign_role_to_user(db: AsyncSession, user_id: str, role_id: str, assigned_by: Optional[str] = None, expires_at: Optional[datetime] = None) -> bool:
    """Assign a role to a user."""
    # Check if already assigned
    from .models import user_role_association
    
    existing = await db.execute(
        select(user_role_association)
        .where(and_(
            user_role_association.c.user_id == user_id,
            user_role_association.c.role_id == role_id
        ))
    )
    
    if existing.first():
        return False  # Already assigned
    
    await db.execute(
        user_role_association.insert().values(
            user_id=user_id,
            role_id=role_id,
            assigned_by=assigned_by,
            expires_at=expires_at,
            assigned_at=datetime.utcnow()
        )
    )
    await db.commit()
    return True

async def remove_role_from_user(db: AsyncSession, user_id: str, role_id: str) -> bool:
    """Remove a role from a user."""
    from .models import user_role_association
    
    result = await db.execute(
        delete(user_role_association)
        .where(and_(
            user_role_association.c.user_id == user_id,
            user_role_association.c.role_id == role_id
        ))
    )
    await db.commit()
    return result.rowcount > 0

async def get_user_roles(db: AsyncSession, user_id: str) -> List[Role]:
    """Get all roles assigned to a user."""
    from .models import user_role_association
    
    result = await db.execute(
        select(Role)
        .join(user_role_association, Role.id == user_role_association.c.role_id)
        .where(user_role_association.c.user_id == user_id)
        .order_by(Role.level, Role.name)
    )
    return result.scalars().all()


# Permission CRUD operations
async def create_permission(
    db: AsyncSession,
    name: str,
    display_name: str,
    description: Optional[str] = None,
    resource: str = "",
    action: str = "",
    scope: str = "workspace",
    is_system: bool = False
) -> Permission:
    """Create a new permission."""
    permission = Permission(
        name=name,
        display_name=display_name,
        description=description,
        resource=resource,
        action=action,
        scope=scope,
        is_system=is_system
    )
    db.add(permission)
    await db.commit()
    await db.refresh(permission)
    return permission

async def get_permission(db: AsyncSession, permission_id: str) -> Optional[Permission]:
    """Get a permission by ID."""
    result = await db.execute(select(Permission).where(Permission.id == permission_id))
    return result.scalar_one_or_none()

async def get_permission_by_name(db: AsyncSession, name: str) -> Optional[Permission]:
    """Get a permission by name."""
    result = await db.execute(select(Permission).where(Permission.name == name))
    return result.scalar_one_or_none()

async def get_permissions(db: AsyncSession, resource: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[Permission]:
    """Get permissions with optional resource filtering."""
    query = select(Permission)
    
    if resource:
        query = query.where(Permission.resource == resource)
    
    query = query.order_by(Permission.resource, Permission.action).offset(skip).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()

async def assign_permission_to_role(db: AsyncSession, role_id: str, permission_id: str) -> bool:
    """Assign a permission to a role."""
    from .models import role_permission_association
    
    # Check if already assigned
    existing = await db.execute(
        select(role_permission_association)
        .where(and_(
            role_permission_association.c.role_id == role_id,
            role_permission_association.c.permission_id == permission_id
        ))
    )
    
    if existing.first():
        return False  # Already assigned
    
    await db.execute(
        role_permission_association.insert().values(
            role_id=role_id,
            permission_id=permission_id
        )
    )
    await db.commit()
    return True

async def remove_permission_from_role(db: AsyncSession, role_id: str, permission_id: str) -> bool:
    """Remove a permission from a role."""
    from .models import role_permission_association
    
    result = await db.execute(
        delete(role_permission_association)
        .where(and_(
            role_permission_association.c.role_id == role_id,
            role_permission_association.c.permission_id == permission_id
        ))
    )
    await db.commit()
    return result.rowcount > 0

async def get_role_permissions(db: AsyncSession, role_id: str) -> List[Permission]:
    """Get all permissions assigned to a role."""
    from .models import role_permission_association
    
    result = await db.execute(
        select(Permission)
        .join(role_permission_association, Permission.id == role_permission_association.c.permission_id)
        .where(role_permission_association.c.role_id == role_id)
        .order_by(Permission.resource, Permission.action)
    )
    return result.scalars().all()

async def get_user_permissions(db: AsyncSession, user_id: str) -> List[Permission]:
    """Get all permissions for a user (through their roles)."""
    from .models import user_role_association, role_permission_association
    
    result = await db.execute(
        select(Permission)
        .join(role_permission_association, Permission.id == role_permission_association.c.permission_id)
        .join(user_role_association, role_permission_association.c.role_id == user_role_association.c.role_id)
        .where(user_role_association.c.user_id == user_id)
        .distinct()
        .order_by(Permission.resource, Permission.action)
    )
    return result.scalars().all()


# Workspace CRUD operations
async def create_workspace(
    db: AsyncSession,
    name: str,
    display_name: str,
    slug: str,
    owner_id: str,
    description: Optional[str] = None,
    is_public: bool = False,
    plan: str = "free"
) -> Workspace:
    """Create a new workspace."""
    workspace = Workspace(
        name=name,
        display_name=display_name,
        slug=slug,
        owner_id=owner_id,
        description=description,
        is_public=is_public,
        plan=plan
    )
    db.add(workspace)
    await db.commit()
    await db.refresh(workspace)
    return workspace

async def get_workspace(db: AsyncSession, workspace_id: str) -> Optional[Workspace]:
    """Get a workspace by ID."""
    result = await db.execute(select(Workspace).where(Workspace.id == workspace_id))
    return result.scalar_one_or_none()

async def get_workspace_by_slug(db: AsyncSession, slug: str) -> Optional[Workspace]:
    """Get a workspace by slug."""
    result = await db.execute(select(Workspace).where(Workspace.slug == slug))
    return result.scalar_one_or_none()

async def get_user_workspaces(db: AsyncSession, user_id: str) -> List[Workspace]:
    """Get all workspaces a user is a member of or owns."""
    from .models import user_workspace_association
    
    # Get owned workspaces
    owned_result = await db.execute(
        select(Workspace)
        .where(Workspace.owner_id == user_id)
    )
    owned_workspaces = owned_result.scalars().all()
    
    # Get member workspaces
    member_result = await db.execute(
        select(Workspace)
        .join(user_workspace_association, Workspace.id == user_workspace_association.c.workspace_id)
        .where(user_workspace_association.c.user_id == user_id)
    )
    member_workspaces = member_result.scalars().all()
    
    # Combine and deduplicate
    all_workspaces = list({w.id: w for w in owned_workspaces + member_workspaces}.values())
    return sorted(all_workspaces, key=lambda w: w.name)

async def add_user_to_workspace(
    db: AsyncSession,
    workspace_id: str,
    user_id: str,
    role_id: str,
    invited_by: Optional[str] = None
) -> bool:
    """Add a user to a workspace with a specific role."""
    from .models import user_workspace_association
    
    # Check if already a member
    existing = await db.execute(
        select(user_workspace_association)
        .where(and_(
            user_workspace_association.c.workspace_id == workspace_id,
            user_workspace_association.c.user_id == user_id
        ))
    )
    
    if existing.first():
        return False  # Already a member
    
    await db.execute(
        user_workspace_association.insert().values(
            workspace_id=workspace_id,
            user_id=user_id,
            role_id=role_id,
            invited_by=invited_by,
            joined_at=datetime.utcnow()
        )
    )
    await db.commit()
    return True

async def remove_user_from_workspace(db: AsyncSession, workspace_id: str, user_id: str) -> bool:
    """Remove a user from a workspace."""
    from .models import user_workspace_association
    
    result = await db.execute(
        delete(user_workspace_association)
        .where(and_(
            user_workspace_association.c.workspace_id == workspace_id,
            user_workspace_association.c.user_id == user_id
        ))
    )
    await db.commit()
    return result.rowcount > 0

async def update_workspace(db: AsyncSession, workspace_id: str, data: Dict[str, Any]) -> Optional[Workspace]:
    """Update a workspace."""
    await db.execute(
        update(Workspace)
        .where(Workspace.id == workspace_id)
        .values(**data, updated_at=datetime.utcnow())
    )
    await db.commit()
    return await get_workspace(db, workspace_id)

async def delete_workspace(db: AsyncSession, workspace_id: str) -> bool:
    """Delete a workspace."""
    await db.execute(delete(Workspace).where(Workspace.id == workspace_id))
    await db.commit()
    return True


# Audit Log CRUD operations
async def create_audit_log(
    db: AsyncSession,
    user_id: Optional[str],
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    workspace_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    session_id: Optional[str] = None,
    old_values: Optional[Dict[str, Any]] = None,
    new_values: Optional[Dict[str, Any]] = None,
    meta_data: Optional[Dict[str, Any]] = None,
    risk_level: str = "low",
    is_suspicious: bool = False
) -> AuditLog:
    """Create an audit log entry."""
    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        workspace_id=workspace_id,
        ip_address=ip_address,
        user_agent=user_agent,
        session_id=session_id,
        old_values=old_values,
        new_values=new_values,
        meta_data=meta_data,
        risk_level=risk_level,
        is_suspicious=is_suspicious
    )
    db.add(audit_log)
    await db.commit()
    await db.refresh(audit_log)
    return audit_log

async def get_audit_logs(
    db: AsyncSession,
    user_id: Optional[str] = None,
    workspace_id: Optional[str] = None,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100
) -> List[AuditLog]:
    """Get audit logs with filtering."""
    query = select(AuditLog)
    
    conditions = []
    if user_id:
        conditions.append(AuditLog.user_id == user_id)
    if workspace_id:
        conditions.append(AuditLog.workspace_id == workspace_id)
    if action:
        conditions.append(AuditLog.action == action)
    if resource_type:
        conditions.append(AuditLog.resource_type == resource_type)
    if start_date:
        conditions.append(AuditLog.timestamp >= start_date)
    if end_date:
        conditions.append(AuditLog.timestamp <= end_date)
    
    if conditions:
        query = query.where(and_(*conditions))
    
    query = query.order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()


# Utility functions for RBAC
async def user_has_permission(
    db: AsyncSession,
    user_id: str,
    permission_name: str,
    workspace_id: Optional[str] = None
) -> bool:
    """Check if a user has a specific permission."""
    # Get user's permissions
    permissions = await get_user_permissions(db, user_id)
    
    # Check for exact permission name match
    for perm in permissions:
        if perm.name == permission_name:
            # For workspace-scoped permissions, check workspace context
            if perm.scope == "workspace" and workspace_id:
                # Additional workspace membership check could be added here
                return True
            elif perm.scope == "global":
                return True
            elif perm.scope == "own":
                # For "own" scope, additional resource ownership check needed
                return True
    
    return False

async def user_has_role(db: AsyncSession, user_id: str, role_name: str) -> bool:
    """Check if a user has a specific role."""
    roles = await get_user_roles(db, user_id)
    return any(role.name == role_name for role in roles)

async def is_workspace_member(db: AsyncSession, user_id: str, workspace_id: str) -> bool:
    """Check if a user is a member of a workspace."""
    from .models import user_workspace_association
    
    # Check ownership
    workspace = await get_workspace(db, workspace_id)
    if workspace and workspace.owner_id == user_id:
        return True
    
    # Check membership
    result = await db.execute(
        select(user_workspace_association)
        .where(and_(
            user_workspace_association.c.user_id == user_id,
            user_workspace_association.c.workspace_id == workspace_id
        ))
    )
    
    return result.first() is not None


async def get_conversations(
    db: AsyncSession, 
    skip: int = 0, 
    limit: int = 20,
    filters: Optional[Dict[str, Any]] = None,
    include_messages: bool = False,
    include_threads: bool = False
) -> List[Conversation]:
    """Get conversations with filtering and pagination."""
    from .models import user_conversation_association
    
    # Start with base query
    query = select(Conversation)
    
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