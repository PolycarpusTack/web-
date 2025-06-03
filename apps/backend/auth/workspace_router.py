"""
Workspace Management API endpoints.
Provides team collaboration and workspace management for enterprise features.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from datetime import datetime
import secrets
import string

from db.database import get_db
from db.crud import (
    # Workspace operations
    create_workspace, get_workspace, get_workspace_by_slug, get_user_workspaces,
    add_user_to_workspace, remove_user_from_workspace,
    
    # User operations
    get_user, get_user_by_email, get_users,
    
    # Role operations
    get_role_by_name, get_user_roles, assign_role_to_user,
    
    # Audit operations
    create_audit_log,
    
    # Utility functions
    is_workspace_member, user_has_permission,
    
    # Conversation operations
    get_conversations
)
from .jwt import get_current_user
from .schemas import UserResponse

router = APIRouter(prefix="/workspaces", tags=["Workspaces"])


# Pydantic schemas for workspace management
from pydantic import BaseModel, validator
from typing import Optional, List

class WorkspaceCreate(BaseModel):
    name: str
    display_name: str
    description: Optional[str] = None
    is_public: bool = False
    plan: str = "free"
    
    @validator('name')
    def validate_name(cls, v):
        # Convert to lowercase slug
        slug = v.lower().replace(' ', '-').replace('_', '-')
        # Remove special characters except hyphens
        slug = ''.join(c for c in slug if c.isalnum() or c == '-')
        # Remove consecutive hyphens
        while '--' in slug:
            slug = slug.replace('--', '-')
        # Remove leading/trailing hyphens
        slug = slug.strip('-')
        
        if len(slug) < 3:
            raise ValueError('Workspace name must be at least 3 characters long')
        if len(slug) > 50:
            raise ValueError('Workspace name must be 50 characters or less')
        
        return slug

class WorkspaceUpdate(BaseModel):
    display_name: Optional[str] = None
    description: Optional[str] = None
    is_public: Optional[bool] = None
    plan: Optional[str] = None

class WorkspaceResponse(BaseModel):
    id: str
    name: str
    display_name: str
    description: Optional[str]
    slug: str
    owner_id: str
    is_active: bool
    is_public: bool
    plan: str
    created_at: datetime
    member_count: Optional[int] = None
    
    class Config:
        from_attributes = True

class WorkspaceMember(BaseModel):
    user_id: str
    username: str
    email: str
    full_name: Optional[str]
    role: str
    joined_at: datetime
    is_owner: bool

class WorkspaceInvite(BaseModel):
    email: str
    role: str = "user"
    message: Optional[str] = None

class WorkspaceStats(BaseModel):
    total_conversations: int
    total_messages: int
    total_pipelines: int
    total_files: int
    monthly_usage_cost: float
    active_members: int

class WorkspaceSettings(BaseModel):
    default_model: Optional[str] = None
    allow_external_sharing: bool = True
    require_approval_for_joins: bool = False
    max_file_size_mb: int = 100
    retention_days: Optional[int] = None
    backup_enabled: bool = True
    notifications_enabled: bool = True

class WorkspaceUsageLimits(BaseModel):
    max_conversations_per_month: Optional[int] = None
    max_messages_per_conversation: Optional[int] = None
    max_file_storage_gb: Optional[int] = None
    max_monthly_cost: Optional[float] = None


# Utility functions
def generate_invite_token() -> str:
    """Generate a secure invite token."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(32))

async def require_workspace_permission(permission: str, workspace_id: str = None):
    """Dependency to check workspace-specific permissions."""
    async def check_permission(
        current_user: UserResponse = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
        request: Request = None
    ):
        # Check if user has global permission
        has_global_perm = await user_has_permission(db, current_user.id, permission)
        if has_global_perm:
            return current_user
        
        # Check workspace membership if workspace_id provided
        if workspace_id:
            is_member = await is_workspace_member(db, current_user.id, workspace_id)
            if not is_member:
                raise HTTPException(
                    status_code=403,
                    detail="Not a member of this workspace"
                )
            
            # Check workspace-specific permission
            has_workspace_perm = await user_has_permission(db, current_user.id, permission, workspace_id)
            if has_workspace_perm:
                return current_user
        
        # Log access denial
        await create_audit_log(
            db=db,
            user_id=current_user.id,
            action="access_denied",
            resource_type="workspace",
            resource_id=workspace_id,
            ip_address=request.client.host if request else None,
            user_agent=request.headers.get("user-agent") if request else None,
            risk_level="medium",
            meta_data={"required_permission": permission}
        )
        
        raise HTTPException(
            status_code=403,
            detail=f"Insufficient permissions. Required: {permission}"
        )
    return check_permission


# Workspace CRUD Endpoints
@router.post("/", response_model=WorkspaceResponse)
async def create_workspace_endpoint(
    workspace_data: WorkspaceCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    request: Request = None
):
    """Create a new workspace."""
    # Check if slug already exists
    existing = await get_workspace_by_slug(db, workspace_data.name)
    if existing:
        raise HTTPException(status_code=400, detail="Workspace name already taken")
    
    # Create workspace
    workspace = await create_workspace(
        db=db,
        name=workspace_data.name,
        display_name=workspace_data.display_name,
        slug=workspace_data.name,
        owner_id=current_user.id,
        description=workspace_data.description,
        is_public=workspace_data.is_public,
        plan=workspace_data.plan
    )
    
    # Assign owner role to creator
    owner_role = await get_role_by_name(db, "admin")
    if owner_role:
        await assign_role_to_user(db, current_user.id, owner_role.id, assigned_by=current_user.id)
    
    # Audit log
    await create_audit_log(
        db=db,
        user_id=current_user.id,
        action="create",
        resource_type="workspace",
        resource_id=workspace.id,
        workspace_id=workspace.id,
        ip_address=request.client.host if request else None,
        user_agent=request.headers.get("user-agent") if request else None,
        new_values={
            "name": workspace.name,
            "display_name": workspace.display_name,
            "plan": workspace.plan
        }
    )
    
    return workspace

@router.get("/", response_model=List[WorkspaceResponse])
async def list_user_workspaces(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all workspaces the current user has access to."""
    workspaces = await get_user_workspaces(db, current_user.id)
    
    # Add member count for each workspace
    workspace_responses = []
    for workspace in workspaces:
        workspace_dict = {
            "id": workspace.id,
            "name": workspace.name,
            "display_name": workspace.display_name,
            "description": workspace.description,
            "slug": workspace.slug,
            "owner_id": workspace.owner_id,
            "is_active": workspace.is_active,
            "is_public": workspace.is_public,
            "plan": workspace.plan,
            "created_at": workspace.created_at,
            "member_count": len(workspace.members) + (1 if workspace.owner else 0)  # Members + owner
        }
        workspace_responses.append(WorkspaceResponse(**workspace_dict))
    
    return workspace_responses

@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace_endpoint(
    workspace_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get workspace details."""
    # Check permission
    has_permission = await user_has_permission(db, current_user.id, "workspaces.read", workspace_id)
    if not has_permission:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    workspace = await get_workspace(db, workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    # Add member count
    workspace_dict = {
        "id": workspace.id,
        "name": workspace.name,
        "display_name": workspace.display_name,
        "description": workspace.description,
        "slug": workspace.slug,
        "owner_id": workspace.owner_id,
        "is_active": workspace.is_active,
        "is_public": workspace.is_public,
        "plan": workspace.plan,
        "created_at": workspace.created_at,
        "member_count": len(workspace.members) + (1 if workspace.owner else 0)
    }
    
    return WorkspaceResponse(**workspace_dict)

@router.put("/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace_endpoint(
    workspace_id: str,
    workspace_data: WorkspaceUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    request: Request = None
):
    """Update workspace details."""
    # Check permission
    has_permission = await user_has_permission(db, current_user.id, "workspaces.update", workspace_id)
    if not has_permission:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    workspace = await get_workspace(db, workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    # Prepare update data
    update_data = {k: v for k, v in workspace_data.dict(exclude_unset=True).items()}
    
    # Update workspace
    from db.crud import update_workspace
    updated_workspace = await update_workspace(db, workspace_id, update_data)
    
    # Audit log
    await create_audit_log(
        db=db,
        user_id=current_user.id,
        action="update",
        resource_type="workspace",
        resource_id=workspace_id,
        workspace_id=workspace_id,
        ip_address=request.client.host if request else None,
        user_agent=request.headers.get("user-agent") if request else None,
        old_values={"display_name": workspace.display_name},
        new_values=update_data
    )
    
    return updated_workspace

@router.delete("/{workspace_id}")
async def delete_workspace_endpoint(
    workspace_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    request: Request = None
):
    """Delete a workspace."""
    workspace = await get_workspace(db, workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    # Only owner can delete workspace
    if workspace.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only workspace owner can delete workspace")
    
    # Delete workspace
    from db.crud import delete_workspace
    success = await delete_workspace(db, workspace_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to delete workspace")
    
    # Audit log
    await create_audit_log(
        db=db,
        user_id=current_user.id,
        action="delete",
        resource_type="workspace",
        resource_id=workspace_id,
        ip_address=request.client.host if request else None,
        user_agent=request.headers.get("user-agent") if request else None,
        old_values={
            "name": workspace.name,
            "display_name": workspace.display_name
        }
    )
    
    return {"message": "Workspace deleted successfully"}


# Member Management Endpoints
@router.get("/{workspace_id}/members", response_model=List[WorkspaceMember])
async def get_workspace_members(
    workspace_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all members of a workspace."""
    workspace = await get_workspace(db, workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    members = []
    
    # Add owner
    if workspace.owner:
        owner_roles = await get_user_roles(db, workspace.owner.id)
        primary_role = owner_roles[0].name if owner_roles else "admin"
        
        members.append(WorkspaceMember(
            user_id=workspace.owner.id,
            username=workspace.owner.username,
            email=workspace.owner.email,
            full_name=workspace.owner.full_name,
            role=primary_role,
            joined_at=workspace.created_at,
            is_owner=True
        ))
    
    # Add members
    from db.models import user_workspace_association
    from sqlalchemy import select
    
    # Get member details with join dates
    result = await db.execute(
        select(user_workspace_association)
        .where(user_workspace_association.c.workspace_id == workspace_id)
    )
    memberships = result.fetchall()
    
    for membership in memberships:
        user = await get_user(db, membership.user_id)
        if user:
            user_roles = await get_user_roles(db, user.id)
            primary_role = user_roles[0].name if user_roles else "user"
            
            members.append(WorkspaceMember(
                user_id=user.id,
                username=user.username,
                email=user.email,
                full_name=user.full_name,
                role=primary_role,
                joined_at=membership.joined_at,
                is_owner=False
            ))
    
    return members

@router.post("/{workspace_id}/members")
async def add_workspace_member(
    workspace_id: str,
    member_data: Dict[str, str],  # {"user_id": "...", "role": "..."}
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    request: Request = None
):
    """Add a user to workspace."""
    workspace = await get_workspace(db, workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    user_id = member_data.get("user_id")
    role_name = member_data.get("role", "user")
    
    # Validate user exists
    user = await get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Validate role exists
    role = await get_role_by_name(db, role_name)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    # Add user to workspace
    success = await add_user_to_workspace(
        db, workspace_id, user_id, role.id, invited_by=current_user.id
    )
    if not success:
        raise HTTPException(status_code=400, detail="User is already a member of this workspace")
    
    # Assign role to user
    await assign_role_to_user(db, user_id, role.id, assigned_by=current_user.id)
    
    # Audit log
    await create_audit_log(
        db=db,
        user_id=current_user.id,
        action="invite_user",
        resource_type="workspace",
        resource_id=workspace_id,
        workspace_id=workspace_id,
        ip_address=request.client.host if request else None,
        user_agent=request.headers.get("user-agent") if request else None,
        new_values={
            "invited_user_id": user_id,
            "invited_user_email": user.email,
            "role": role_name
        }
    )
    
    return {"message": f"User {user.username} added to workspace successfully"}

@router.delete("/{workspace_id}/members/{user_id}")
async def remove_workspace_member(
    workspace_id: str,
    user_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    request: Request = None
):
    """Remove a user from workspace."""
    workspace = await get_workspace(db, workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    # Cannot remove workspace owner
    if workspace.owner_id == user_id:
        raise HTTPException(status_code=400, detail="Cannot remove workspace owner")
    
    # Users can remove themselves
    if current_user.id != user_id:
        # Check if current user has permission to manage users
        has_permission = await user_has_permission(db, current_user.id, "users.manage", workspace_id)
        if not has_permission:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    user = await get_user(db, user_id)
    success = await remove_user_from_workspace(db, workspace_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User is not a member of this workspace")
    
    # Audit log
    await create_audit_log(
        db=db,
        user_id=current_user.id,
        action="remove_user",
        resource_type="workspace",
        resource_id=workspace_id,
        workspace_id=workspace_id,
        ip_address=request.client.host if request else None,
        user_agent=request.headers.get("user-agent") if request else None,
        old_values={
            "removed_user_id": user_id,
            "removed_user_email": user.email if user else "unknown"
        }
    )
    
    return {"message": "User removed from workspace successfully"}


# Workspace Statistics
@router.get("/{workspace_id}/stats", response_model=WorkspaceStats)
async def get_workspace_stats(
    workspace_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get workspace usage statistics."""
    workspace = await get_workspace(db, workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    # Get basic counts
    from sqlalchemy import func, select
    from db.models import Conversation, Message, File, Pipeline, UsageRecord
    from datetime import datetime, timedelta
    
    # Count conversations
    conv_result = await db.execute(
        select(func.count(Conversation.id))
        .where(Conversation.workspace_id == workspace_id)
    )
    total_conversations = conv_result.scalar() or 0
    
    # Count messages in workspace conversations
    msg_result = await db.execute(
        select(func.count(Message.id))
        .join(Conversation, Message.conversation_id == Conversation.id)
        .where(Conversation.workspace_id == workspace_id)
    )
    total_messages = msg_result.scalar() or 0
    
    # Count pipelines
    pip_result = await db.execute(
        select(func.count(Pipeline.id))
        .where(Pipeline.workspace_id == workspace_id)
    )
    total_pipelines = pip_result.scalar() or 0
    
    # Count files
    file_result = await db.execute(
        select(func.count(File.id))
        .join(Conversation, File.conversation_id == Conversation.id)
        .where(Conversation.workspace_id == workspace_id)
    )
    total_files = file_result.scalar() or 0
    
    # Calculate monthly usage cost
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    cost_result = await db.execute(
        select(func.sum(UsageRecord.cost))
        .join(Conversation, UsageRecord.execution_id == Conversation.id)  # Simplified join
        .where(
            Conversation.workspace_id == workspace_id,
            UsageRecord.created_at >= thirty_days_ago
        )
    )
    monthly_usage_cost = float(cost_result.scalar() or 0.0)
    
    # Count active members (including owner)
    active_members = len(workspace.members) + (1 if workspace.owner else 0)
    
    return WorkspaceStats(
        total_conversations=total_conversations,
        total_messages=total_messages,
        total_pipelines=total_pipelines,
        total_files=total_files,
        monthly_usage_cost=monthly_usage_cost,
        active_members=active_members
    )


# Workspace Settings
@router.get("/{workspace_id}/settings", response_model=WorkspaceSettings)
async def get_workspace_settings(
    workspace_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get workspace settings."""
    workspace = await get_workspace(db, workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    # Extract settings from workspace.settings JSON field
    settings = workspace.settings or {}
    
    return WorkspaceSettings(
        default_model=settings.get("default_model"),
        allow_external_sharing=settings.get("allow_external_sharing", True),
        require_approval_for_joins=settings.get("require_approval_for_joins", False),
        max_file_size_mb=settings.get("max_file_size_mb", 100),
        retention_days=settings.get("retention_days"),
        backup_enabled=settings.get("backup_enabled", True),
        notifications_enabled=settings.get("notifications_enabled", True)
    )

@router.put("/{workspace_id}/settings", response_model=WorkspaceSettings)
async def update_workspace_settings(
    workspace_id: str,
    settings_data: WorkspaceSettings,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    request: Request = None
):
    """Update workspace settings."""
    workspace = await get_workspace(db, workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    # Convert settings to dict
    new_settings = settings_data.dict()
    
    # Update workspace settings
    from db.crud import update_workspace
    await update_workspace(db, workspace_id, {"settings": new_settings})
    
    # Audit log
    await create_audit_log(
        db=db,
        user_id=current_user.id,
        action="update_settings",
        resource_type="workspace",
        resource_id=workspace_id,
        workspace_id=workspace_id,
        ip_address=request.client.host if request else None,
        user_agent=request.headers.get("user-agent") if request else None,
        old_values=workspace.settings,
        new_values=new_settings
    )
    
    return settings_data


# Public workspace discovery
@router.get("/public/discover", response_model=List[WorkspaceResponse])
async def discover_public_workspaces(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Discover public workspaces."""
    from sqlalchemy import select, or_
    from db.models import Workspace
    
    query = select(Workspace).where(Workspace.is_public == True, Workspace.is_active == True)
    
    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                Workspace.display_name.ilike(search_term),
                Workspace.description.ilike(search_term)
            )
        )
    
    query = query.order_by(Workspace.created_at.desc()).offset(skip).limit(limit)
    
    result = await db.execute(query)
    workspaces = result.scalars().all()
    
    # Convert to response format
    workspace_responses = []
    for workspace in workspaces:
        workspace_dict = {
            "id": workspace.id,
            "name": workspace.name,
            "display_name": workspace.display_name,
            "description": workspace.description,
            "slug": workspace.slug,
            "owner_id": workspace.owner_id,
            "is_active": workspace.is_active,
            "is_public": workspace.is_public,
            "plan": workspace.plan,
            "created_at": workspace.created_at,
            "member_count": len(workspace.members) + (1 if workspace.owner else 0)
        }
        workspace_responses.append(WorkspaceResponse(**workspace_dict))
    
    return workspace_responses