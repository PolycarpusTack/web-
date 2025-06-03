"""
Workspace Invitation Management API endpoints.
Handles team invitations and onboarding for enterprise collaboration.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, EmailStr
import secrets
import string

from db.database import get_db
from db.crud import (
    get_workspace, get_user_by_email, get_role_by_name,
    add_user_to_workspace, assign_role_to_user, create_audit_log,
    user_has_permission, create_user
)
from .jwt import get_current_user
from .schemas import UserResponse
from .password import hash_password

router = APIRouter(prefix="/invitations", tags=["Invitations"])


# Import the WorkspaceInvitation model
from db.models import WorkspaceInvitation


# Pydantic schemas
class InvitationCreate(BaseModel):
    email: EmailStr
    role: str = "user"
    message: Optional[str] = None

class InvitationResponse(BaseModel):
    id: str
    workspace_id: str
    email: str
    role: str
    message: Optional[str]
    status: str
    created_at: datetime
    expires_at: datetime
    invited_by: str
    workspace_name: Optional[str] = None
    inviter_name: Optional[str] = None
    
    class Config:
        from_attributes = True

class InvitationAccept(BaseModel):
    token: str
    create_account: bool = False
    password: Optional[str] = None
    full_name: Optional[str] = None


def generate_invitation_token() -> str:
    """Generate a secure invitation token."""
    alphabet = string.ascii_letters + string.digits + '-_'
    return ''.join(secrets.choice(alphabet) for _ in range(48))


async def send_invitation_email(email: str, workspace_name: str, inviter_name: str, token: str, message: str = None):
    """Send invitation email (placeholder for email service integration)."""
    # In a real implementation, this would integrate with an email service
    print(f"Sending invitation email to {email}")
    print(f"Workspace: {workspace_name}")
    print(f"Invited by: {inviter_name}")
    print(f"Token: {token}")
    if message:
        print(f"Message: {message}")
    print(f"Accept invitation: http://localhost:3000/invite/{token}")


# Create invitation
@router.post("/{workspace_id}/invite", response_model=InvitationResponse)
async def create_invitation(
    workspace_id: str,
    invitation_data: InvitationCreate,
    background_tasks: BackgroundTasks,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    request: Request = None
):
    """Create a workspace invitation."""
    # Check if user has permission to invite users
    has_permission = await user_has_permission(db, current_user.id, "users.invite", workspace_id)
    if not has_permission:
        raise HTTPException(status_code=403, detail="Insufficient permissions to invite users")
    
    # Check if workspace exists
    workspace = await get_workspace(db, workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    # Check if role exists
    role = await get_role_by_name(db, invitation_data.role)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    # Check if user is already a member
    existing_user = await get_user_by_email(db, invitation_data.email)
    if existing_user:
        from db.crud import is_workspace_member
        if await is_workspace_member(db, existing_user.id, workspace_id):
            raise HTTPException(status_code=400, detail="User is already a member of this workspace")
    
    # Check for existing pending invitation
    from sqlalchemy import select, and_
    existing_invitation = await db.execute(
        select(WorkspaceInvitation)
        .where(and_(
            WorkspaceInvitation.workspace_id == workspace_id,
            WorkspaceInvitation.email == invitation_data.email,
            WorkspaceInvitation.status == "pending"
        ))
    )
    if existing_invitation.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Invitation already sent to this email")
    
    # Create invitation
    token = generate_invitation_token()
    expires_at = datetime.utcnow() + timedelta(days=7)  # 7 days to accept
    
    invitation = WorkspaceInvitation(
        workspace_id=workspace_id,
        email=invitation_data.email,
        token=token,
        role=invitation_data.role,
        message=invitation_data.message,
        invited_by=current_user.id,
        expires_at=expires_at
    )
    
    db.add(invitation)
    await db.commit()
    await db.refresh(invitation)
    
    # Send invitation email in background
    background_tasks.add_task(
        send_invitation_email,
        invitation_data.email,
        workspace.display_name,
        current_user.username,
        token,
        invitation_data.message
    )
    
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
            "email": invitation_data.email,
            "role": invitation_data.role,
            "invitation_id": invitation.id
        }
    )
    
    return InvitationResponse(
        id=invitation.id,
        workspace_id=workspace_id,
        email=invitation_data.email,
        role=invitation_data.role,
        message=invitation_data.message,
        status="pending",
        created_at=invitation.created_at,
        expires_at=invitation.expires_at,
        invited_by=current_user.id,
        workspace_name=workspace.display_name,
        inviter_name=current_user.username
    )


# Get invitation by token
@router.get("/token/{token}", response_model=InvitationResponse)
async def get_invitation_by_token(
    token: str,
    db: AsyncSession = Depends(get_db)
):
    """Get invitation details by token."""
    from sqlalchemy import select
    
    result = await db.execute(
        select(WorkspaceInvitation)
        .where(WorkspaceInvitation.token == token)
    )
    invitation = result.scalar_one_or_none()
    
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")
    
    if invitation.status != "pending":
        raise HTTPException(status_code=400, detail="Invitation is no longer valid")
    
    if invitation.expires_at < datetime.utcnow():
        # Mark as expired
        invitation.status = "expired"
        await db.commit()
        raise HTTPException(status_code=400, detail="Invitation has expired")
    
    # Get workspace and inviter details
    workspace = await get_workspace(db, invitation.workspace_id)
    from db.crud import get_user
    inviter = await get_user(db, invitation.invited_by)
    
    return InvitationResponse(
        id=invitation.id,
        workspace_id=invitation.workspace_id,
        email=invitation.email,
        role=invitation.role,
        message=invitation.message,
        status=invitation.status,
        created_at=invitation.created_at,
        expires_at=invitation.expires_at,
        invited_by=invitation.invited_by,
        workspace_name=workspace.display_name if workspace else None,
        inviter_name=inviter.username if inviter else None
    )


# Accept invitation
@router.post("/accept")
async def accept_invitation(
    acceptance_data: InvitationAccept,
    db: AsyncSession = Depends(get_db),
    request: Request = None
):
    """Accept a workspace invitation."""
    from sqlalchemy import select
    
    # Get invitation
    result = await db.execute(
        select(WorkspaceInvitation)
        .where(WorkspaceInvitation.token == acceptance_data.token)
    )
    invitation = result.scalar_one_or_none()
    
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")
    
    if invitation.status != "pending":
        raise HTTPException(status_code=400, detail="Invitation is no longer valid")
    
    if invitation.expires_at < datetime.utcnow():
        invitation.status = "expired"
        await db.commit()
        raise HTTPException(status_code=400, detail="Invitation has expired")
    
    # Check if user exists
    user = await get_user_by_email(db, invitation.email)
    
    if not user and acceptance_data.create_account:
        # Create new user account
        if not acceptance_data.password or not acceptance_data.full_name:
            raise HTTPException(
                status_code=400, 
                detail="Password and full name required to create account"
            )
        
        # Generate username from email
        username = invitation.email.split('@')[0]
        counter = 1
        original_username = username
        
        # Ensure username is unique
        from db.crud import get_user_by_username
        while await get_user_by_username(db, username):
            username = f"{original_username}{counter}"
            counter += 1
        
        # Create user
        hashed_password = hash_password(acceptance_data.password)
        user = await create_user(
            db=db,
            username=username,
            email=invitation.email,
            hashed_password=hashed_password,
            full_name=acceptance_data.full_name
        )
    
    if not user:
        raise HTTPException(
            status_code=400, 
            detail="User account not found. Please create an account first or use create_account option."
        )
    
    # Get role
    role = await get_role_by_name(db, invitation.role)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    # Add user to workspace
    success = await add_user_to_workspace(
        db, invitation.workspace_id, user.id, role.id, invited_by=invitation.invited_by
    )
    
    if success:
        # Assign role to user
        await assign_role_to_user(db, user.id, role.id, assigned_by=invitation.invited_by)
        
        # Mark invitation as accepted
        invitation.status = "accepted"
        invitation.accepted_at = datetime.utcnow()
        invitation.accepted_by = user.id
        await db.commit()
        
        # Audit log
        await create_audit_log(
            db=db,
            user_id=user.id,
            action="accept_invitation",
            resource_type="workspace",
            resource_id=invitation.workspace_id,
            workspace_id=invitation.workspace_id,
            ip_address=request.client.host if request else None,
            user_agent=request.headers.get("user-agent") if request else None,
            new_values={
                "invitation_id": invitation.id,
                "role": invitation.role
            }
        )
        
        return {"message": "Invitation accepted successfully", "user_id": user.id}
    else:
        raise HTTPException(status_code=400, detail="Failed to add user to workspace")


# List workspace invitations
@router.get("/{workspace_id}", response_model=List[InvitationResponse])
async def list_workspace_invitations(
    workspace_id: str,
    status: Optional[str] = None,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all invitations for a workspace."""
    # Check permission
    has_permission = await user_has_permission(db, current_user.id, "users.read", workspace_id)
    if not has_permission:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    from sqlalchemy import select
    
    query = select(WorkspaceInvitation).where(WorkspaceInvitation.workspace_id == workspace_id)
    
    if status:
        query = query.where(WorkspaceInvitation.status == status)
    
    query = query.order_by(WorkspaceInvitation.created_at.desc())
    
    result = await db.execute(query)
    invitations = result.scalars().all()
    
    # Convert to response format
    invitation_responses = []
    workspace = await get_workspace(db, workspace_id)
    
    for invitation in invitations:
        from db.crud import get_user
        inviter = await get_user(db, invitation.invited_by)
        
        invitation_responses.append(InvitationResponse(
            id=invitation.id,
            workspace_id=invitation.workspace_id,
            email=invitation.email,
            role=invitation.role,
            message=invitation.message,
            status=invitation.status,
            created_at=invitation.created_at,
            expires_at=invitation.expires_at,
            invited_by=invitation.invited_by,
            workspace_name=workspace.display_name if workspace else None,
            inviter_name=inviter.username if inviter else None
        ))
    
    return invitation_responses


# Cancel invitation
@router.delete("/{invitation_id}")
async def cancel_invitation(
    invitation_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    request: Request = None
):
    """Cancel a workspace invitation."""
    from sqlalchemy import select
    
    # Get invitation
    result = await db.execute(
        select(WorkspaceInvitation)
        .where(WorkspaceInvitation.id == invitation_id)
    )
    invitation = result.scalar_one_or_none()
    
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")
    
    # Check permission
    has_permission = await user_has_permission(db, current_user.id, "users.manage", invitation.workspace_id)
    if not has_permission and invitation.invited_by != current_user.id:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    if invitation.status != "pending":
        raise HTTPException(status_code=400, detail="Can only cancel pending invitations")
    
    # Cancel invitation
    invitation.status = "cancelled"
    await db.commit()
    
    # Audit log
    await create_audit_log(
        db=db,
        user_id=current_user.id,
        action="cancel_invitation",
        resource_type="workspace",
        resource_id=invitation.workspace_id,
        workspace_id=invitation.workspace_id,
        ip_address=request.client.host if request else None,
        user_agent=request.headers.get("user-agent") if request else None,
        old_values={
            "invitation_id": invitation.id,
            "email": invitation.email
        }
    )
    
    return {"message": "Invitation cancelled successfully"}