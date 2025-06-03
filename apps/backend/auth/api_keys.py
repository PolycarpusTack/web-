from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import logging
import secrets
from datetime import datetime, timedelta

from db.database import get_db
from db import crud
from db.models import User, APIKey as ApiKey
from auth.jwt import get_current_active_user
from pydantic import BaseModel, Field

# Set up logging
logger = logging.getLogger(__name__)

# Create the router
router = APIRouter(
    prefix="/api/api-keys",
    tags=["api keys"],
    responses={
        401: {"description": "Unauthorized"},
        404: {"description": "Not found"},
    },
)

# API key models
class ApiKeyCreate(BaseModel):
    """Model for creating an API key."""
    name: str = Field(..., min_length=1, max_length=100)
    expires_in_days: Optional[int] = None

class ApiKeyResponse(BaseModel):
    """Model for API key response."""
    id: str
    name: str
    key: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    is_active: bool

    class Config:
        orm_mode = True

class ApiKeyInfo(BaseModel):
    """Model for API key info (without the key itself)."""
    id: str
    name: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    is_active: bool

    class Config:
        orm_mode = True

# API key endpoints
@router.post("", response_model=ApiKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    api_key_data: ApiKeyCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new API key for the current user.
    The key will be returned once and cannot be retrieved again.
    """
    # Generate a random API key
    key = secrets.token_urlsafe(32)
    
    # Calculate expiration date if provided
    expires_at = None
    if api_key_data.expires_in_days is not None:
        expires_at = datetime.utcnow() + timedelta(days=api_key_data.expires_in_days)
    
    # Create the API key
    api_key = await crud.create_api_key(
        db=db,
        user_id=current_user.id,
        key=key,
        name=api_key_data.name,
        expires_at=expires_at
    )
    
    return api_key

@router.get("", response_model=List[ApiKeyInfo])
async def list_api_keys(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all API keys for the current user.
    Note that the actual key values are not returned for security reasons.
    """
    api_keys = await crud.get_user_api_keys(db, current_user.id)
    return api_keys

@router.delete("/{api_key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    api_key_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete an API key.
    """
    # Get the API key
    api_key = await crud.get_api_key_by_id(db, api_key_id)
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    # Check if the API key belongs to the current user
    if api_key.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this API key"
        )
    
    # Delete the API key
    await crud.delete_api_key(db, api_key_id)
    
    return None

@router.put("/{api_key_id}/revoke", response_model=ApiKeyInfo)
async def revoke_api_key(
    api_key_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Revoke an API key without deleting it.
    """
    # Get the API key
    api_key = await crud.get_api_key_by_id(db, api_key_id)
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    # Check if the API key belongs to the current user
    if api_key.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to revoke this API key"
        )
    
    # Revoke the API key
    updated_key = await crud.update_api_key(
        db=db,
        api_key_id=api_key_id,
        data={"is_active": False}
    )
    
    return updated_key
