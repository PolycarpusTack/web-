"""
Conversation Management API

This module provides advanced conversation management including:
- Folder organization
- Sharing and collaboration
- Bookmarks and templates
- Activity tracking
"""
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, func
from sqlalchemy.orm import selectinload
from pydantic import BaseModel, Field

from db.database import get_db
from db.models import (
    User, Conversation, ConversationFolder, ConversationShare, 
    ConversationCollaborator, ConversationActivity, ConversationTemplate,
    ConversationBookmark, PermissionLevel, ShareType
)
from auth.jwt import get_current_user
from core.cache import cache_manager, CacheNamespaces
import logging

logger = logging.getLogger(__name__)

# Pydantic Models
class FolderCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    icon: Optional[str] = Field(None, max_length=50)
    parent_folder_id: Optional[str] = None

class FolderUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    icon: Optional[str] = Field(None, max_length=50)
    parent_folder_id: Optional[str] = None

class FolderResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    color: Optional[str]
    icon: Optional[str]
    owner_id: str
    parent_folder_id: Optional[str]
    is_system: bool
    is_shared: bool
    created_at: datetime
    updated_at: Optional[datetime]
    conversation_count: int = 0
    sub_folder_count: int = 0

class ShareCreate(BaseModel):
    conversation_id: str
    share_type: ShareType
    shared_with_id: Optional[str] = None
    team_id: Optional[str] = None
    permission_level: PermissionLevel = PermissionLevel.READ
    expires_at: Optional[datetime] = None

class ShareResponse(BaseModel):
    id: str
    conversation_id: str
    share_type: ShareType
    share_token: Optional[str]
    shared_by_id: str
    shared_with_id: Optional[str]
    permission_level: PermissionLevel
    expires_at: Optional[datetime]
    is_active: bool
    access_count: int
    created_at: datetime

class CollaboratorInvite(BaseModel):
    conversation_id: str
    user_id: str
    permission_level: PermissionLevel = PermissionLevel.READ

class CollaboratorResponse(BaseModel):
    id: str
    conversation_id: str
    user_id: str
    username: str
    permission_level: PermissionLevel
    invited_by_id: str
    invited_at: datetime
    accepted_at: Optional[datetime]
    is_active: bool

class TemplateCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    model_id: str
    system_prompt: Optional[str] = None
    initial_messages: Optional[List[Dict[str, Any]]] = None
    settings: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    is_public: bool = False

class TemplateResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    creator_id: str
    model_id: str
    model_name: str
    system_prompt: Optional[str]
    settings: Optional[Dict[str, Any]]
    tags: Optional[List[str]]
    is_public: bool
    is_featured: bool
    usage_count: int
    created_at: datetime

class ConversationMoveRequest(BaseModel):
    conversation_ids: List[str]
    folder_id: Optional[str] = None  # None means move to root

class BookmarkCreate(BaseModel):
    conversation_id: str
    note: Optional[str] = Field(None, max_length=500)

class ConversationSearchRequest(BaseModel):
    query: Optional[str] = None
    folder_id: Optional[str] = None
    shared_only: bool = False
    bookmarked_only: bool = False
    model_ids: Optional[List[str]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    sort_by: str = "updated_at"
    sort_direction: str = "desc"
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)

class ConversationSearchResponse(BaseModel):
    conversations: List[Dict[str, Any]]
    total_count: int
    page: int
    page_size: int
    total_pages: int

# Business Logic Classes
class ConversationManager:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_folder(self, user: User, data: FolderCreate) -> ConversationFolder:
        """Create a new conversation folder."""
        # Check if parent folder exists and user has access
        if data.parent_folder_id:
            parent = await self.db.get(ConversationFolder, data.parent_folder_id)
            if not parent or parent.owner_id != user.id:
                raise HTTPException(400, "Parent folder not found or access denied")
        
        folder = ConversationFolder(
            name=data.name,
            description=data.description,
            color=data.color,
            icon=data.icon,
            owner_id=user.id,
            parent_folder_id=data.parent_folder_id
        )
        
        self.db.add(folder)
        await self.db.commit()
        await self.db.refresh(folder)
        
        # Log activity
        await self._log_activity(
            conversation_id=None,
            user_id=user.id,
            activity_type="folder_created",
            description=f"Created folder '{folder.name}'"
        )
        
        # Clear cache for user folders
        await cache_manager.delete(CacheNamespaces.CONVERSATIONS, f"user_folders_{user.id}_True")
        await cache_manager.delete(CacheNamespaces.CONVERSATIONS, f"user_folders_{user.id}_False")
        
        return folder
    
    async def get_user_folders(self, user: User, include_conversations: bool = False) -> List[ConversationFolder]:
        """Get all folders owned by the user."""
        # Try cache first
        cache_key = f"user_folders_{user.id}_{include_conversations}"
        cached_folders = await cache_manager.get(CacheNamespaces.CONVERSATIONS, cache_key)
        if cached_folders is not None:
            logger.debug(f"Cache hit for user folders: {user.id}")
            return cached_folders
        
        query = select(ConversationFolder).where(ConversationFolder.owner_id == user.id)
        
        if include_conversations:
            query = query.options(selectinload(ConversationFolder.conversations))
        
        result = await self.db.execute(query.order_by(ConversationFolder.name))
        folders = result.scalars().all()
        
        # Cache the result
        await cache_manager.set(CacheNamespaces.CONVERSATIONS, cache_key, folders, ttl=300)
        logger.debug(f"Cached user folders: {user.id}")
        
        return folders
    
    async def move_conversations_to_folder(self, user: User, request: ConversationMoveRequest) -> Dict[str, Any]:
        """Move conversations to a folder."""
        # Verify folder ownership if moving to a folder
        if request.folder_id:
            folder = await self.db.get(ConversationFolder, request.folder_id)
            if not folder or folder.owner_id != user.id:
                raise HTTPException(400, "Folder not found or access denied")
        
        # Get conversations and verify ownership
        query = select(Conversation).where(
            and_(
                Conversation.id.in_(request.conversation_ids),
                Conversation.users.any(User.id == user.id)
            )
        )
        result = await self.db.execute(query)
        conversations = result.scalars().all()
        
        if len(conversations) != len(request.conversation_ids):
            raise HTTPException(400, "Some conversations not found or access denied")
        
        # Update folder associations
        moved_count = 0
        for conversation in conversations:
            if request.folder_id:
                # Add to folder if not already there
                if request.folder_id not in [f.id for f in conversation.folders]:
                    conversation.folders.append(folder)
                    moved_count += 1
            else:
                # Remove from all folders (move to root)
                conversation.folders.clear()
                moved_count += 1
        
        await self.db.commit()
        
        # Clear cache for affected conversations and folders
        for conv_id in request.conversation_ids:
            await cache_manager.delete(CacheNamespaces.CONVERSATIONS, f"conversation_{conv_id}")
        await cache_manager.delete(CacheNamespaces.CONVERSATIONS, f"user_folders_{user.id}_True")
        await cache_manager.delete(CacheNamespaces.CONVERSATIONS, f"user_folders_{user.id}_False")
        
        return {
            "moved_count": moved_count,
            "folder_id": request.folder_id,
            "folder_name": folder.name if request.folder_id else "Root"
        }
    
    async def create_share(self, user: User, data: ShareCreate) -> ConversationShare:
        """Create a conversation share."""
        # Verify conversation ownership or collaboration permission
        conversation = await self.db.get(Conversation, data.conversation_id)
        if not conversation:
            raise HTTPException(404, "Conversation not found")
        
        # Check if user has permission to share
        has_permission = False
        if any(u.id == user.id for u in conversation.users):
            has_permission = True
        
        if not has_permission:
            # Check if user is a collaborator with admin permission
            collab_query = select(ConversationCollaborator).where(
                and_(
                    ConversationCollaborator.conversation_id == data.conversation_id,
                    ConversationCollaborator.user_id == user.id,
                    ConversationCollaborator.permission_level == PermissionLevel.ADMIN
                )
            )
            collab_result = await self.db.execute(collab_query)
            if collab_result.scalar():
                has_permission = True
        
        if not has_permission:
            raise HTTPException(403, "Permission denied to share this conversation")
        
        share = ConversationShare(
            conversation_id=data.conversation_id,
            share_type=data.share_type,
            shared_by_id=user.id,
            shared_with_id=data.shared_with_id,
            team_id=data.team_id,
            permission_level=data.permission_level,
            expires_at=data.expires_at
        )
        
        # Generate share token for link sharing
        if data.share_type in [ShareType.LINK, ShareType.PUBLIC]:
            share.share_token = str(uuid4())
        
        self.db.add(share)
        await self.db.commit()
        await self.db.refresh(share)
        
        # Log activity
        await self._log_activity(
            conversation_id=data.conversation_id,
            user_id=user.id,
            activity_type="conversation_shared",
            description=f"Shared conversation with {data.share_type.value} access"
        )
        
        return share
    
    async def search_conversations(self, user: User, request: ConversationSearchRequest) -> ConversationSearchResponse:
        """Search user's conversations with filters."""
        # Generate cache key from search parameters
        cache_key = f"search_{user.id}_{hash(str(request.dict()))}"
        cached_result = await cache_manager.get(CacheNamespaces.CONVERSATIONS, cache_key)
        if cached_result is not None:
            logger.debug(f"Cache hit for conversation search: {user.id}")
            return cached_result
        
        query = select(Conversation).options(
            selectinload(Conversation.model),
            selectinload(Conversation.folders),
            selectinload(Conversation.bookmarks)
        )
        
        # Base filter: user has access
        query = query.where(Conversation.users.any(User.id == user.id))
        
        # Apply filters
        if request.query:
            search_term = f"%{request.query}%"
            query = query.where(
                or_(
                    Conversation.title.ilike(search_term),
                    Conversation.system_prompt.ilike(search_term)
                )
            )
        
        if request.folder_id:
            query = query.where(Conversation.folders.any(ConversationFolder.id == request.folder_id))
        
        if request.shared_only:
            query = query.where(Conversation.shares.any(ConversationShare.is_active == True))
        
        if request.bookmarked_only:
            query = query.where(
                Conversation.bookmarks.any(
                    and_(
                        ConversationBookmark.user_id == user.id,
                        ConversationBookmark.id.isnot(None)
                    )
                )
            )
        
        if request.model_ids:
            query = query.where(Conversation.model_id.in_(request.model_ids))
        
        if request.date_from:
            query = query.where(Conversation.created_at >= request.date_from)
        
        if request.date_to:
            query = query.where(Conversation.created_at <= request.date_to)
        
        # Count total results
        count_query = select(func.count()).select_from(query.subquery())
        total_count = (await self.db.execute(count_query)).scalar()
        
        # Apply sorting and pagination
        if request.sort_direction.lower() == "desc":
            query = query.order_by(desc(getattr(Conversation, request.sort_by)))
        else:
            query = query.order_by(getattr(Conversation, request.sort_by))
        
        offset = (request.page - 1) * request.page_size
        query = query.offset(offset).limit(request.page_size)
        
        result = await self.db.execute(query)
        conversations = result.scalars().all()
        
        # Format response
        conversation_data = []
        for conv in conversations:
            data = {
                "id": conv.id,
                "title": conv.title,
                "model_id": conv.model_id,
                "model_name": conv.model.name if conv.model else None,
                "created_at": conv.created_at,
                "updated_at": conv.updated_at,
                "message_count": len(conv.messages),
                "folders": [{"id": f.id, "name": f.name} for f in conv.folders],
                "is_bookmarked": any(b.user_id == user.id for b in conv.bookmarks),
                "is_shared": len(conv.shares) > 0
            }
            conversation_data.append(data)
        
        total_pages = (total_count + request.page_size - 1) // request.page_size
        
        result = ConversationSearchResponse(
            conversations=conversation_data,
            total_count=total_count,
            page=request.page,
            page_size=request.page_size,
            total_pages=total_pages
        )
        
        # Cache the search result with shorter TTL (2 minutes)
        await cache_manager.set(CacheNamespaces.CONVERSATIONS, cache_key, result, ttl=120)
        logger.debug(f"Cached conversation search: {user.id}")
        
        return result
    
    async def _log_activity(self, conversation_id: Optional[str], user_id: str, activity_type: str, description: str):
        """Log an activity."""
        activity = ConversationActivity(
            conversation_id=conversation_id,
            user_id=user_id,
            activity_type=activity_type,
            description=description
        )
        self.db.add(activity)
        # Don't commit here - let the calling method handle it

# Router
router = APIRouter(prefix="/api/conversations", tags=["Conversation Management"])

# Folder Management
@router.post("/folders", response_model=FolderResponse)
async def create_folder(
    data: FolderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new conversation folder."""
    manager = ConversationManager(db)
    folder = await manager.create_folder(current_user, data)
    
    return FolderResponse(
        id=folder.id,
        name=folder.name,
        description=folder.description,
        color=folder.color,
        icon=folder.icon,
        owner_id=folder.owner_id,
        parent_folder_id=folder.parent_folder_id,
        is_system=folder.is_system,
        is_shared=folder.is_shared,
        created_at=folder.created_at,
        updated_at=folder.updated_at
    )

@router.get("/folders", response_model=List[FolderResponse])
async def get_user_folders(
    include_conversations: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's conversation folders."""
    manager = ConversationManager(db)
    folders = await manager.get_user_folders(current_user, include_conversations)
    
    return [
        FolderResponse(
            id=folder.id,
            name=folder.name,
            description=folder.description,
            color=folder.color,
            icon=folder.icon,
            owner_id=folder.owner_id,
            parent_folder_id=folder.parent_folder_id,
            is_system=folder.is_system,
            is_shared=folder.is_shared,
            created_at=folder.created_at,
            updated_at=folder.updated_at,
            conversation_count=len(folder.conversations) if include_conversations else 0
        )
        for folder in folders
    ]

@router.post("/move")
async def move_conversations(
    request: ConversationMoveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Move conversations to a folder."""
    manager = ConversationManager(db)
    return await manager.move_conversations_to_folder(current_user, request)

# Sharing
@router.post("/share", response_model=ShareResponse)
async def create_share(
    data: ShareCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a conversation share."""
    manager = ConversationManager(db)
    share = await manager.create_share(current_user, data)
    
    return ShareResponse(
        id=share.id,
        conversation_id=share.conversation_id,
        share_type=share.share_type,
        share_token=share.share_token,
        shared_by_id=share.shared_by_id,
        shared_with_id=share.shared_with_id,
        permission_level=share.permission_level,
        expires_at=share.expires_at,
        is_active=share.is_active,
        access_count=share.access_count,
        created_at=share.created_at
    )

# Search
@router.post("/search", response_model=ConversationSearchResponse)
async def search_conversations(
    request: ConversationSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search conversations with advanced filters."""
    manager = ConversationManager(db)
    return await manager.search_conversations(current_user, request)

# Bookmarks
@router.post("/bookmark")
async def create_bookmark(
    data: BookmarkCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Bookmark a conversation."""
    # Check if conversation exists and user has access
    conversation = await db.get(Conversation, data.conversation_id)
    if not conversation or not any(u.id == current_user.id for u in conversation.users):
        raise HTTPException(404, "Conversation not found or access denied")
    
    # Check if already bookmarked
    existing_query = select(ConversationBookmark).where(
        and_(
            ConversationBookmark.user_id == current_user.id,
            ConversationBookmark.conversation_id == data.conversation_id
        )
    )
    existing = (await db.execute(existing_query)).scalar()
    
    if existing:
        raise HTTPException(400, "Conversation already bookmarked")
    
    bookmark = ConversationBookmark(
        user_id=current_user.id,
        conversation_id=data.conversation_id,
        note=data.note
    )
    
    db.add(bookmark)
    await db.commit()
    
    # Clear conversation cache
    await cache_manager.delete(CacheNamespaces.CONVERSATIONS, f"conversation_{data.conversation_id}")
    
    return {"message": "Conversation bookmarked successfully"}

@router.delete("/bookmark/{conversation_id}")
async def remove_bookmark(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove a bookmark."""
    query = select(ConversationBookmark).where(
        and_(
            ConversationBookmark.user_id == current_user.id,
            ConversationBookmark.conversation_id == conversation_id
        )
    )
    bookmark = (await db.execute(query)).scalar()
    
    if not bookmark:
        raise HTTPException(404, "Bookmark not found")
    
    await db.delete(bookmark)
    await db.commit()
    
    # Clear conversation cache
    await cache_manager.delete(CacheNamespaces.CONVERSATIONS, f"conversation_{conversation_id}")
    
    return {"message": "Bookmark removed successfully"}