from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import logging

from db.database import get_db
from db import crud
from db.models import User
from auth.jwt import (
    create_tokens, 
    get_current_user, 
    get_current_active_user,
    get_current_superuser,
    verify_refresh_token,
    Token, 
    RefreshToken,
    TokenResponse
)
from auth.password import hash_password, verify_password, evaluate_password_strength
from auth.schemas import (
    UserCreate, 
    UserResponse, 
    UserUpdate, 
    LoginRequest, 
    RegistrationRequest,
    ChangePasswordRequest,
    ResetPasswordRequest,
    RequestPasswordResetRequest,
    UserInfo
)

# Set up logging
logger = logging.getLogger(__name__)

# Create the router
router = APIRouter(
    prefix="/api/auth",
    tags=["authentication"],
    responses={
        401: {"description": "Unauthorized"},
        404: {"description": "Not found"},
    },
)

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    registration: RegistrationRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user.
    """
    # Check if username already exists
    existing_user = await crud.get_user_by_username(db, registration.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    existing_email = await crud.get_user_by_email(db, registration.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if passwords match
    if registration.password != registration.password_confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match"
        )
    
    # Check password strength
    password_strength = evaluate_password_strength(registration.password)
    if not password_strength.passes_requirements:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password not strong enough: {', '.join(password_strength.issues)}"
        )
    
    # Hash the password
    hashed_password = hash_password(registration.password)
    
    # Create the user
    user = await crud.create_user(
        db=db,
        username=registration.username,
        email=registration.email,
        hashed_password=hashed_password,
        full_name=registration.full_name
    )
    
    return user

@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    OAuth2 compatible token login, get an access token for future requests.
    This endpoint is used by the OpenAPI UI.
    """
    # Get the user by username
    user = await crud.get_user_by_username(db, form_data.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify the password
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if the user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create tokens
    tokens = create_tokens(user.id, user.username, form_data.scopes)
    
    return Token(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        token_type=tokens.token_type,
        expires_at=tokens.expires_at
    )

@router.post("/login", response_model=Token)
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Login a user with username and password.
    Returns access and refresh tokens.
    """
    # Get the user by username
    user = await crud.get_user_by_username(db, login_data.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify the password
    if not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if the user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create tokens
    tokens = create_tokens(user.id, user.username)
    
    return Token(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        token_type=tokens.token_type,
        expires_at=tokens.expires_at
    )

@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token_data: RefreshToken,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a new access token using a refresh token.
    """
    # Verify the refresh token
    payload = await verify_refresh_token(refresh_token_data.refresh_token, db)
    
    # Get the user
    user = await crud.get_user_by_username(db, payload["sub"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create new tokens
    tokens = create_tokens(user.id, user.username)
    
    return Token(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        token_type=tokens.token_type,
        expires_at=tokens.expires_at
    )

@router.get("/me", response_model=UserInfo)
async def read_users_me(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get information about the currently authenticated user.
    """
    return current_user

@router.put("/me", response_model=UserInfo)
async def update_user_me(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update the current user's information.
    """
    # Remove fields that the user is not allowed to update
    if hasattr(user_update, "is_superuser"):
        delattr(user_update, "is_superuser")
    
    # Update the user
    updated_user = await crud.update_user(
        db=db,
        user_id=current_user.id,
        data=user_update.dict(exclude_unset=True)
    )
    
    return updated_user

@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Change the current user's password.
    """
    # Verify the current password
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if passwords match
    if password_data.new_password != password_data.new_password_confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match"
        )
    
    # Check password strength
    password_strength = evaluate_password_strength(password_data.new_password)
    if not password_strength.passes_requirements:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password not strong enough: {', '.join(password_strength.issues)}"
        )
    
    # Hash the new password
    hashed_password = hash_password(password_data.new_password)
    
    # Update the user's password
    await crud.update_user(
        db=db,
        user_id=current_user.id,
        data={"hashed_password": hashed_password}
    )
    
    return None

@router.post("/request-password-reset", status_code=status.HTTP_204_NO_CONTENT)
async def request_password_reset(
    request_data: RequestPasswordResetRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Request a password reset.
    In a real implementation, this would send an email with a reset link.
    """
    # Find the user by email
    user = await crud.get_user_by_email(db, request_data.email)
    if not user:
        # Don't reveal that the email doesn't exist, just return success
        return None
    
    # In a real implementation, generate a token and send an email
    # For now, just log a message
    logger.info(f"Password reset requested for user: {user.username}")
    
    return None

# Admin only routes
@router.get("/users", response_model=List[UserInfo])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a list of users. Admin only.
    """
    users = await crud.get_users(db, skip=skip, limit=limit)
    return users

@router.get("/users/{user_id}", response_model=UserInfo)
async def read_user(
    user_id: str,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific user by ID. Admin only.
    """
    user = await crud.get_user(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@router.put("/users/{user_id}", response_model=UserInfo)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a user. Admin only.
    """
    user = await crud.get_user(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    updated_user = await crud.update_user(
        db=db,
        user_id=user_id,
        data=user_update.dict(exclude_unset=True)
    )
    
    return updated_user

@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a user. Admin only.
    """
    user = await crud.get_user(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if trying to delete self
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself"
        )
    
    await crud.delete_user(db, user_id)
    
    return None
