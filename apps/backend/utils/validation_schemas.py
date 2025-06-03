"""
API validation schemas for input validation.
This module provides Pydantic models for validating API request and response data.
"""

from pydantic import BaseModel, Field, validator, EmailStr, constr, root_validator
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import re
from enum import Enum

# User schemas
class UserBase(BaseModel):
    """Base model for user data."""
    
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = Field(None, max_length=100)

class UserCreate(UserBase):
    """Schema for creating a new user."""
    
    password: str = Field(..., min_length=8, max_length=100)
    password_confirm: str = Field(..., min_length=8, max_length=100)
    
    @root_validator
    def validate_passwords_match(cls, values):
        """Validate that passwords match."""
        password = values.get("password")
        password_confirm = values.get("password_confirm")
        
        if password != password_confirm:
            raise ValueError("Passwords do not match")
            
        # Check for password strength
        if password:
            # Require at least one uppercase, one lowercase, one digit, and one special char
            if not re.match(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$", password):
                raise ValueError("Password must contain uppercase, lowercase, digit, and special character")
                
        return values

class UserUpdate(BaseModel):
    """Schema for updating a user."""
    
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None

class UserResponse(UserBase):
    """Schema for user response data."""
    
    id: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    role: str
    
    class Config:
        orm_mode = True

# Authentication schemas
class LoginRequest(BaseModel):
    """Schema for login request."""
    
    username: str
    password: str

class TokenResponse(BaseModel):
    """Schema for authentication token response."""
    
    access_token: str
    refresh_token: str
    token_type: str
    expires_at: datetime

class RefreshTokenRequest(BaseModel):
    """Schema for token refresh request."""
    
    refresh_token: str

class ChangePasswordRequest(BaseModel):
    """Schema for password change request."""
    
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)
    new_password_confirm: str = Field(..., min_length=8, max_length=100)
    
    @root_validator
    def validate_passwords_match(cls, values):
        """Validate that new passwords match."""
        new_password = values.get("new_password")
        new_password_confirm = values.get("new_password_confirm")
        
        if new_password != new_password_confirm:
            raise ValueError("New passwords do not match")
            
        # Check for password strength
        if new_password:
            # Require at least one uppercase, one lowercase, one digit, and one special char
            if not re.match(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$", new_password):
                raise ValueError("Password must contain uppercase, lowercase, digit, and special character")
                
        return values

# API Key schemas
class APIKeyCreate(BaseModel):
    """Schema for creating a new API key."""
    
    name: str = Field(..., min_length=1, max_length=100)
    expires_in_days: Optional[int] = Field(None, ge=1)

class APIKeyResponse(BaseModel):
    """Schema for API key response data."""
    
    id: str
    name: str
    key: Optional[str] = None  # Only included when creating a new key
    created_at: datetime
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    is_active: bool
    
    class Config:
        orm_mode = True

# Model schemas
class ModelBase(BaseModel):
    """Base model for LLM model data."""
    
    id: str
    name: str
    provider: str
    description: Optional[str] = None
    version: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    capabilities: Optional[Dict[str, Any]] = None
    context_window: int
    max_output_tokens: Optional[int] = None
    pricing: Optional[Dict[str, Any]] = None

class ModelCreate(ModelBase):
    """Schema for creating a new model."""
    
    pass

class ModelUpdate(BaseModel):
    """Schema for updating a model."""
    
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    parameters: Optional[Dict[str, Any]] = None
    capabilities: Optional[Dict[str, Any]] = None
    context_window: Optional[int] = None
    max_output_tokens: Optional[int] = None
    pricing: Optional[Dict[str, Any]] = None

class ModelResponse(ModelBase):
    """Schema for model response data."""
    
    id: str
    name: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True

# Conversation schemas
class MessageRole(str, Enum):
    """Enum for message roles."""
    
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"

class ConversationBase(BaseModel):
    """Base model for conversation data."""
    
    title: str = Field(..., min_length=1, max_length=200)
    model_id: str
    system_prompt: Optional[str] = None

class ConversationCreate(ConversationBase):
    """Schema for creating a new conversation."""
    
    pass

class ConversationUpdate(BaseModel):
    """Schema for updating a conversation."""
    
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    system_prompt: Optional[str] = None

class MessageBase(BaseModel):
    """Base model for message data."""
    
    content: str
    role: MessageRole
    metadata: Optional[Dict[str, Any]] = None
    parent_id: Optional[str] = None
    thread_id: Optional[str] = None

class MessageCreate(MessageBase):
    """Schema for creating a new message."""
    
    conversation_id: str

class MessageUpdate(BaseModel):
    """Schema for updating a message."""
    
    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class MessageResponse(MessageBase):
    """Schema for message response data."""
    
    id: str
    conversation_id: str
    created_at: datetime
    tokens: Optional[int] = None
    cost: Optional[float] = None
    user_id: Optional[str] = None
    
    class Config:
        orm_mode = True

class ConversationResponse(ConversationBase):
    """Schema for conversation response data."""
    
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    messages: Optional[List[MessageResponse]] = None
    
    class Config:
        orm_mode = True

# Thread schemas
class ThreadBase(BaseModel):
    """Base model for thread data."""
    
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    conversation_id: str
    parent_thread_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class ThreadCreate(ThreadBase):
    """Schema for creating a new thread."""
    
    pass

class ThreadUpdate(BaseModel):
    """Schema for updating a thread."""
    
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    metadata: Optional[Dict[str, Any]] = None

class ThreadResponse(ThreadBase):
    """Schema for thread response data."""
    
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    creator_id: Optional[str] = None
    messages: Optional[List[MessageResponse]] = None
    
    class Config:
        orm_mode = True

# File schemas
class FileBase(BaseModel):
    """Base model for file data."""
    
    original_filename: str
    content_type: str
    size: int
    is_public: bool = False
    metadata: Optional[Dict[str, Any]] = None

class FileCreate(FileBase):
    """Schema for creating a new file."""
    
    conversation_id: Optional[str] = None

class FileUpdate(BaseModel):
    """Schema for updating a file."""
    
    original_filename: Optional[str] = None
    is_public: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None

class FileResponse(FileBase):
    """Schema for file response data."""
    
    id: str
    filename: str  # Internal filename
    created_at: datetime
    user_id: str
    conversation_id: Optional[str] = None
    analyzed: bool
    analysis_result: Optional[Dict[str, Any]] = None
    
    class Config:
        orm_mode = True

# Chat completion schemas
class ChatCompletionOptions(BaseModel):
    """Schema for chat completion options."""
    
    temperature: Optional[float] = Field(None, ge=0.0, le=1.0)
    max_tokens: Optional[int] = Field(None, ge=1)
    top_p: Optional[float] = Field(None, ge=0.0, le=1.0)
    frequency_penalty: Optional[float] = Field(None, ge=0.0, le=2.0)
    presence_penalty: Optional[float] = Field(None, ge=0.0, le=2.0)
    stop: Optional[Union[str, List[str]]] = None

class ChatCompletionRequest(BaseModel):
    """Schema for chat completion request."""
    
    model_id: str
    prompt: str
    system_prompt: Optional[str] = None
    options: Optional[ChatCompletionOptions] = None
    conversation_id: Optional[str] = None
    stream: bool = False

class ChatCompletionUsage(BaseModel):
    """Schema for chat completion usage data."""
    
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    prompt_cost: float
    completion_cost: float
    total_cost: float

class ChatCompletionResponse(BaseModel):
    """Schema for chat completion response."""
    
    id: str
    model: str
    created: int  # Unix timestamp
    content: str
    processing_time: float
    usage: ChatCompletionResponse
    conversation_id: Optional[str] = None

# File analysis schemas
class FileAnalysisRequest(BaseModel):
    """Schema for file analysis request."""
    
    file_id: str

class FileAnalysisResponse(BaseModel):
    """Schema for file analysis response."""
    
    id: str
    analyzed: bool
    analysis_status: str
    analysis_result: Optional[Dict[str, Any]] = None
    extracted_text: Optional[str] = None
    extraction_quality: Optional[float] = None
    progress: Optional[float] = None
    estimated_completion_time: Optional[datetime] = None
