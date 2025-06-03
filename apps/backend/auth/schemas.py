from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import re

class UserBase(BaseModel):
    """Base model for user data."""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool = True
    
    @validator('username')
    def username_alphanumeric(cls, v):
        """Validate that the username is alphanumeric with underscores allowed."""
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError('Username must contain only letters, numbers, and underscores')
        return v

class UserCreate(UserBase):
    """Model for creating a new user."""
    password: str = Field(..., min_length=8)
    
    @validator('password')
    def password_strength(cls, v):
        """Validate that the password is strong enough."""
        from auth.password import evaluate_password_strength
        
        strength = evaluate_password_strength(v)
        if not strength.passes_requirements:
            issues = ", ".join(strength.issues)
            raise ValueError(f"Password is not strong enough: {issues}")
        return v

class UserUpdate(BaseModel):
    """Model for updating a user."""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None

class UserResponse(UserBase):
    """Model for user response."""
    id: str
    is_superuser: bool = False
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        
    @validator('is_superuser', pre=True)
    def validate_is_superuser(cls, v):
        """Ensure is_superuser is always a boolean."""
        if v is None:
            return False
        return bool(v)

class UserInDB(UserResponse):
    """Model for user in database."""
    hashed_password: str
    
    class Config:
        orm_mode = True

class LoginRequest(BaseModel):
    """Model for login request."""
    username: str
    password: str

class RegistrationRequest(UserCreate):
    """Model for user registration."""
    password_confirm: str
    
    @validator('password_confirm')
    def passwords_match(cls, v, values, **kwargs):
        """Validate that the passwords match."""
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v

class ChangePasswordRequest(BaseModel):
    """Model for changing a password."""
    current_password: str
    new_password: str
    new_password_confirm: str
    
    @validator('new_password')
    def password_strength(cls, v):
        """Validate that the password is strong enough."""
        from auth.password import evaluate_password_strength
        
        strength = evaluate_password_strength(v)
        if not strength.passes_requirements:
            issues = ", ".join(strength.issues)
            raise ValueError(f"Password is not strong enough: {issues}")
        return v
    
    @validator('new_password_confirm')
    def passwords_match(cls, v, values, **kwargs):
        """Validate that the passwords match."""
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v

class ResetPasswordRequest(BaseModel):
    """Model for resetting a password."""
    token: str
    new_password: str
    new_password_confirm: str
    
    @validator('new_password')
    def password_strength(cls, v):
        """Validate that the password is strong enough."""
        from auth.password import evaluate_password_strength
        
        strength = evaluate_password_strength(v)
        if not strength.passes_requirements:
            issues = ", ".join(strength.issues)
            raise ValueError(f"Password is not strong enough: {issues}")
        return v
    
    @validator('new_password_confirm')
    def passwords_match(cls, v, values, **kwargs):
        """Validate that the passwords match."""
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v

class RequestPasswordResetRequest(BaseModel):
    """Model for requesting a password reset."""
    email: EmailStr

class UserInfo(BaseModel):
    """Model for user info response."""
    id: str
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool
    is_superuser: bool
    created_at: datetime
    
    class Config:
        orm_mode = True
