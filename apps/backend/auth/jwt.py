from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Union
import os
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status, WebSocket, Query
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr

from db.database import get_db
from db.models import User
from db import crud

# Load environment variables or use defaults
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-for-dev-only")  # Change in production
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# OAuth2 password bearer scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/token")

# Token models
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_at: datetime

class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[str] = None
    scopes: list[str] = []

class RefreshToken(BaseModel):
    refresh_token: str
    
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_at: datetime

# Functions for creating and validating tokens
def create_access_token(
    data: Dict[str, Any], 
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: The data to encode in the token
        expires_delta: Optional expiration time delta
        
    Returns:
        The encoded JWT token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT refresh token.
    
    Args:
        data: The data to encode in the token
        expires_delta: Optional expiration time delta
        
    Returns:
        The encoded JWT refresh token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_tokens(user_id: str, username: str, scopes: list[str] = None) -> TokenResponse:
    """
    Create both access and refresh tokens for a user.
    
    Args:
        user_id: The user ID
        username: The username
        scopes: Optional list of permission scopes
        
    Returns:
        TokenResponse with both tokens and expiration
    """
    if scopes is None:
        scopes = []
        
    # Create the access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": username, "id": user_id, "scopes": scopes},
        expires_delta=access_token_expires
    )
    
    # Create the refresh token
    refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = create_refresh_token(
        data={"sub": username, "id": user_id},
        expires_delta=refresh_token_expires
    )
    
    expires_at = datetime.utcnow() + access_token_expires
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_at=expires_at
    )

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Validate the access token and get the current user.
    
    Args:
        token: The JWT token
        db: Database session
        
    Returns:
        The user object
        
    Raises:
        HTTPException: If the token is invalid or the user doesn't exist
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode the JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Check if it's an access token
        if payload.get("type") != "access":
            raise credentials_exception
        
        # Extract user information
        username: str = payload.get("sub")
        user_id: str = payload.get("id")
        
        if username is None or user_id is None:
            raise credentials_exception
            
        token_data = TokenData(username=username, user_id=user_id)
    except JWTError:
        raise credentials_exception
    
    # Get the user from the database
    user = await crud.get_user(db, user_id)
    if user is None:
        raise credentials_exception
    
    # Check if the user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get the current active user.
    
    Args:
        current_user: The current user from the token
        
    Returns:
        The user object if active
        
    Raises:
        HTTPException: If the user is not active
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def verify_refresh_token(
    refresh_token: str,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Verify a refresh token.
    
    Args:
        refresh_token: The refresh token to verify
        db: Database session
        
    Returns:
        The decoded token payload
        
    Raises:
        HTTPException: If the token is invalid
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode the JWT token
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Check if it's a refresh token
        if payload.get("type") != "refresh":
            raise credentials_exception
        
        # Extract user information
        username: str = payload.get("sub")
        user_id: str = payload.get("id")
        
        if username is None or user_id is None:
            raise credentials_exception
            
        # Check if the user exists
        user = await crud.get_user(db, user_id)
        if user is None or not user.is_active:
            raise credentials_exception
            
        return payload
    except JWTError:
        raise credentials_exception

def require_scopes(required_scopes: list[str]):
    """
    Create a dependency that checks if the user has the required scopes.
    
    Args:
        required_scopes: List of required scopes
        
    Returns:
        A dependency function that checks the scopes
    """
    async def scopes_checker(token: str = Depends(oauth2_scheme)):
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            token_scopes = payload.get("scopes", [])
            
            for scope in required_scopes:
                if scope not in token_scopes:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Not enough permissions. Required: {required_scopes}",
                    )
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return True
    
    return scopes_checker

async def get_current_superuser(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get the current user if they are a superuser.
    
    Args:
        current_user: The current user from the token
        
    Returns:
        The user object if they are a superuser
        
    Raises:
        HTTPException: If the user is not a superuser
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return current_user

async def get_current_user_websocket(
    websocket: WebSocket,
    token: str = Query(None, alias="token"),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    WebSocket authentication dependency.
    
    Args:
        websocket: The WebSocket connection
        token: JWT token from query parameter
        db: Database session
        
    Returns:
        The authenticated user
        
    Raises:
        WebSocketException: If authentication fails
    """
    if not token:
        await websocket.close(code=1008, reason="Authentication token required")
        raise HTTPException(401, "Token required")
    
    try:
        # Remove 'Bearer ' prefix if present
        if token.startswith("Bearer "):
            token = token[7:]
        
        # Decode the JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Check if it's an access token
        if payload.get("type") != "access":
            await websocket.close(code=1008, reason="Invalid token type")
            raise HTTPException(401, "Invalid token")
        
        # Extract user information
        username: str = payload.get("sub")
        user_id: str = payload.get("id")
        
        if username is None or user_id is None:
            await websocket.close(code=1008, reason="Invalid token payload")
            raise HTTPException(401, "Invalid token")
        
        # Get the user from the database
        user = await crud.get_user(db, user_id)
        if user is None:
            await websocket.close(code=1008, reason="User not found")
            raise HTTPException(404, "User not found")
        
        # Check if the user is active
        if not user.is_active:
            await websocket.close(code=1008, reason="User account is inactive")
            raise HTTPException(403, "User inactive")
        
        return user
        
    except JWTError:
        await websocket.close(code=1008, reason="Invalid token")
        raise HTTPException(401, "Invalid token")
    except Exception as e:
        await websocket.close(code=1011, reason="Authentication error")
        raise HTTPException(500, f"Authentication error: {str(e)}")
