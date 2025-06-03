"""
RBAC (Role-Based Access Control) API endpoints.
Provides role and permission management for enterprise features.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from datetime import datetime

from db.database import get_db
from db.crud import (
    # Role operations
    create_role, get_role, get_role_by_name, get_roles, update_role, delete_role,
    assign_role_to_user, remove_role_from_user, get_user_roles,
    
    # Permission operations
    create_permission, get_permission, get_permission_by_name, get_permissions,
    assign_permission_to_role, remove_permission_from_role, get_role_permissions,
    get_user_permissions,
    
    # Workspace operations
    create_workspace, get_workspace, get_workspace_by_slug, get_user_workspaces,
    add_user_to_workspace, remove_user_from_workspace,
    
    # Audit operations
    create_audit_log, get_audit_logs,
    
    # Utility functions
    user_has_permission, user_has_role, is_workspace_member,
    
    # User operations
    get_user
)
from .jwt import get_current_user
from .schemas import UserResponse

router = APIRouter(prefix="/rbac", tags=["RBAC"])


# Pydantic schemas for RBAC
from pydantic import BaseModel
from typing import Optional, List

class RoleBase(BaseModel):
    name: str
    display_name: str
    description: Optional[str] = None

class RoleCreate(RoleBase):
    parent_role_id: Optional[str] = None

class RoleUpdate(BaseModel):
    display_name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class RoleResponse(RoleBase):
    id: str
    is_system: bool
    is_active: bool
    level: int
    created_at: datetime
    parent_role_id: Optional[str] = None
    
    class Config:
        from_attributes = True

class PermissionBase(BaseModel):
    name: str
    display_name: str
    description: Optional[str] = None
    resource: str
    action: str
    scope: str = "workspace"

class PermissionCreate(PermissionBase):
    pass

class PermissionResponse(PermissionBase):
    id: str
    is_system: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class WorkspaceBase(BaseModel):
    name: str
    display_name: str
    description: Optional[str] = None
    slug: str

class WorkspaceCreate(WorkspaceBase):
    is_public: bool = False
    plan: str = "free"

class WorkspaceUpdate(BaseModel):
    display_name: Optional[str] = None
    description: Optional[str] = None
    is_public: Optional[bool] = None
    plan: Optional[str] = None

class WorkspaceResponse(WorkspaceBase):
    id: str
    owner_id: str
    is_active: bool
    is_public: bool
    plan: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserRoleAssignment(BaseModel):
    user_id: str
    role_id: str
    expires_at: Optional[datetime] = None

class RolePermissionAssignment(BaseModel):
    role_id: str
    permission_id: str

class WorkspaceMemberAdd(BaseModel):
    user_id: str
    role_id: str

class AuditLogResponse(BaseModel):
    id: str
    user_id: Optional[str]
    action: str
    resource_type: str
    resource_id: Optional[str]
    timestamp: datetime
    workspace_id: Optional[str]
    ip_address: Optional[str]
    risk_level: str
    is_suspicious: bool
    
    class Config:
        from_attributes = True


# Dependency to check if user has permission
def require_permission(permission: str):
    async def check_permission(
        current_user: UserResponse = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
        request: Request = None
    ):
        has_perm = await user_has_permission(db, current_user.id, permission)
        if not has_perm:
            await create_audit_log(
                db=db,
                user_id=current_user.id,
                action="access_denied",
                resource_type="permission",
                resource_id=permission,
                ip_address=request.client.host if request else None,
                user_agent=request.headers.get("user-agent") if request else None,
                risk_level="medium",
                meta_data={"required_permission": permission}
            )
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions. Required: {permission}"
            )
        return current_user
    return check_permission


# Role Management Endpoints
@router.get("/roles", response_model=List[RoleResponse])
async def list_roles(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: UserResponse = Depends(require_permission("users.manage")),
    db: AsyncSession = Depends(get_db)
):
    """List all roles."""
    roles = await get_roles(db, skip=skip, limit=limit)
    return roles

@router.post("/roles", response_model=RoleResponse)
async def create_role_endpoint(
    role_data: RoleCreate,
    current_user: UserResponse = Depends(require_permission("users.manage")),
    db: AsyncSession = Depends(get_db),
    request: Request = None
):
    """Create a new role."""
    # Check if role name already exists
    existing = await get_role_by_name(db, role_data.name)
    if existing:
        raise HTTPException(status_code=400, detail="Role name already exists")
    
    role = await create_role(
        db=db,
        name=role_data.name,
        display_name=role_data.display_name,
        description=role_data.description,
        parent_role_id=role_data.parent_role_id,
        created_by=current_user.id
    )
    
    # Audit log
    await create_audit_log(
        db=db,
        user_id=current_user.id,
        action="create",
        resource_type="role",
        resource_id=role.id,
        ip_address=request.client.host if request else None,
        user_agent=request.headers.get("user-agent") if request else None,
        new_values={"name": role.name, "display_name": role.display_name}
    )
    
    return role

@router.get("/roles/{role_id}", response_model=RoleResponse)
async def get_role_endpoint(
    role_id: str,
    current_user: UserResponse = Depends(require_permission("users.manage")),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific role."""
    role = await get_role(db, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return role

@router.put("/roles/{role_id}", response_model=RoleResponse)
async def update_role_endpoint(
    role_id: str,
    role_data: RoleUpdate,
    current_user: UserResponse = Depends(require_permission("users.manage")),
    db: AsyncSession = Depends(get_db),
    request: Request = None
):
    """Update a role."""
    existing_role = await get_role(db, role_id)
    if not existing_role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    if existing_role.is_system:
        raise HTTPException(status_code=400, detail="Cannot modify system roles")
    
    # Prepare update data
    update_data = {k: v for k, v in role_data.dict(exclude_unset=True).items()}
    
    role = await update_role(db, role_id, update_data)
    
    # Audit log
    await create_audit_log(
        db=db,
        user_id=current_user.id,
        action="update",
        resource_type="role",
        resource_id=role_id,
        ip_address=request.client.host if request else None,
        user_agent=request.headers.get("user-agent") if request else None,
        old_values={"display_name": existing_role.display_name},
        new_values=update_data
    )
    
    return role

@router.delete("/roles/{role_id}")
async def delete_role_endpoint(
    role_id: str,
    current_user: UserResponse = Depends(require_permission("users.manage")),
    db: AsyncSession = Depends(get_db),
    request: Request = None
):
    """Delete a role."""
    existing_role = await get_role(db, role_id)
    if not existing_role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    success = await delete_role(db, role_id)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot delete system roles")
    
    # Audit log
    await create_audit_log(
        db=db,
        user_id=current_user.id,
        action="delete",
        resource_type="role",
        resource_id=role_id,
        ip_address=request.client.host if request else None,
        user_agent=request.headers.get("user-agent") if request else None,
        old_values={"name": existing_role.name, "display_name": existing_role.display_name}
    )
    
    return {"message": "Role deleted successfully"}


# Permission Management Endpoints
@router.get("/permissions", response_model=List[PermissionResponse])
async def list_permissions(
    resource: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: UserResponse = Depends(require_permission("users.manage")),
    db: AsyncSession = Depends(get_db)
):
    """List all permissions."""
    permissions = await get_permissions(db, resource=resource, skip=skip, limit=limit)
    return permissions

@router.get("/roles/{role_id}/permissions", response_model=List[PermissionResponse])
async def get_role_permissions_endpoint(
    role_id: str,
    current_user: UserResponse = Depends(require_permission("users.manage")),
    db: AsyncSession = Depends(get_db)
):
    """Get permissions assigned to a role."""
    role = await get_role(db, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    permissions = await get_role_permissions(db, role_id)
    return permissions

@router.post("/roles/{role_id}/permissions")
async def assign_permission_to_role_endpoint(
    role_id: str,
    assignment: RolePermissionAssignment,
    current_user: UserResponse = Depends(require_permission("users.manage")),
    db: AsyncSession = Depends(get_db),
    request: Request = None
):
    """Assign a permission to a role."""
    role = await get_role(db, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    permission = await get_permission(db, assignment.permission_id)
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")
    
    success = await assign_permission_to_role(db, role_id, assignment.permission_id)
    if not success:
        raise HTTPException(status_code=400, detail="Permission already assigned to role")
    
    # Audit log
    await create_audit_log(
        db=db,
        user_id=current_user.id,
        action="assign_permission",
        resource_type="role",
        resource_id=role_id,
        ip_address=request.client.host if request else None,
        user_agent=request.headers.get("user-agent") if request else None,
        new_values={"permission_id": assignment.permission_id, "permission_name": permission.name}
    )
    
    return {"message": "Permission assigned to role successfully"}

@router.delete("/roles/{role_id}/permissions/{permission_id}")
async def remove_permission_from_role_endpoint(
    role_id: str,
    permission_id: str,
    current_user: UserResponse = Depends(require_permission("users.manage")),
    db: AsyncSession = Depends(get_db),
    request: Request = None
):
    """Remove a permission from a role."""
    success = await remove_permission_from_role(db, role_id, permission_id)
    if not success:
        raise HTTPException(status_code=404, detail="Permission not assigned to role")
    
    # Audit log
    await create_audit_log(
        db=db,
        user_id=current_user.id,
        action="remove_permission",
        resource_type="role",
        resource_id=role_id,
        ip_address=request.client.host if request else None,
        user_agent=request.headers.get("user-agent") if request else None,
        old_values={"permission_id": permission_id}
    )
    
    return {"message": "Permission removed from role successfully"}


# User Role Management Endpoints
@router.get("/users/{user_id}/roles", response_model=List[RoleResponse])
async def get_user_roles_endpoint(
    user_id: str,
    current_user: UserResponse = Depends(require_permission("users.read")),
    db: AsyncSession = Depends(get_db)
):
    """Get roles assigned to a user."""
    user = await get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    roles = await get_user_roles(db, user_id)
    return roles

@router.post("/users/{user_id}/roles")
async def assign_role_to_user_endpoint(
    user_id: str,
    assignment: UserRoleAssignment,
    current_user: UserResponse = Depends(require_permission("users.manage")),
    db: AsyncSession = Depends(get_db),
    request: Request = None
):
    """Assign a role to a user."""
    user = await get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    role = await get_role(db, assignment.role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    success = await assign_role_to_user(
        db, user_id, assignment.role_id, 
        assigned_by=current_user.id, 
        expires_at=assignment.expires_at
    )
    if not success:
        raise HTTPException(status_code=400, detail="Role already assigned to user")
    
    # Audit log
    await create_audit_log(
        db=db,
        user_id=current_user.id,
        action="assign_role",
        resource_type="user",
        resource_id=user_id,
        ip_address=request.client.host if request else None,
        user_agent=request.headers.get("user-agent") if request else None,
        new_values={"role_id": assignment.role_id, "role_name": role.name}
    )
    
    return {"message": "Role assigned to user successfully"}

@router.delete("/users/{user_id}/roles/{role_id}")
async def remove_role_from_user_endpoint(
    user_id: str,
    role_id: str,
    current_user: UserResponse = Depends(require_permission("users.manage")),
    db: AsyncSession = Depends(get_db),
    request: Request = None
):
    """Remove a role from a user."""
    success = await remove_role_from_user(db, user_id, role_id)
    if not success:
        raise HTTPException(status_code=404, detail="Role not assigned to user")
    
    # Audit log
    await create_audit_log(
        db=db,
        user_id=current_user.id,
        action="remove_role",
        resource_type="user",
        resource_id=user_id,
        ip_address=request.client.host if request else None,
        user_agent=request.headers.get("user-agent") if request else None,
        old_values={"role_id": role_id}
    )
    
    return {"message": "Role removed from user successfully"}


# User Permissions Endpoint
@router.get("/users/{user_id}/permissions", response_model=List[PermissionResponse])
async def get_user_permissions_endpoint(
    user_id: str,
    current_user: UserResponse = Depends(require_permission("users.read")),
    db: AsyncSession = Depends(get_db)
):
    """Get all permissions for a user (through their roles)."""
    user = await get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    permissions = await get_user_permissions(db, user_id)
    return permissions


# Audit Log Endpoints
@router.get("/audit-logs", response_model=List[AuditLogResponse])
async def get_audit_logs_endpoint(
    user_id: Optional[str] = Query(None),
    workspace_id: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: UserResponse = Depends(require_permission("audit.read")),
    db: AsyncSession = Depends(get_db)
):
    """Get audit logs with filtering."""
    logs = await get_audit_logs(
        db=db,
        user_id=user_id,
        workspace_id=workspace_id,
        action=action,
        resource_type=resource_type,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit
    )
    return logs


# Permission Check Endpoint
@router.get("/check-permission/{permission_name}")
async def check_user_permission(
    permission_name: str,
    workspace_id: Optional[str] = Query(None),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Check if current user has a specific permission."""
    has_permission = await user_has_permission(db, current_user.id, permission_name, workspace_id)
    return {"has_permission": has_permission, "permission": permission_name}


# Current User Roles and Permissions
@router.get("/me/roles", response_model=List[RoleResponse])
async def get_my_roles(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's roles."""
    roles = await get_user_roles(db, current_user.id)
    return roles

@router.get("/me/permissions", response_model=List[PermissionResponse])
async def get_my_permissions(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's permissions."""
    permissions = await get_user_permissions(db, current_user.id)
    return permissions