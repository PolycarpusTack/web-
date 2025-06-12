from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Text, JSON, Float, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from datetime import datetime
from .database import Base

# Import extended conversation models
from .conversation_models import (
    ConversationFolder, ConversationShare, ConversationCollaborator,
    ConversationActivity, ConversationTemplate, ConversationBookmark,
    PermissionLevel, ShareType
)

def generate_uuid():
    return str(uuid.uuid4())

# Association tables for many-to-many relationships
model_tag_association = Table(
    "model_tag_association",
    Base.metadata,
    Column("model_id", String, ForeignKey("models.id")),
    Column("tag_id", Integer, ForeignKey("tags.id")),
)

user_conversation_association = Table(
    "user_conversation_association",
    Base.metadata,
    Column("user_id", String, ForeignKey("users.id"), primary_key=True),
    Column("conversation_id", String, ForeignKey("conversations.id"), primary_key=True),
)

# RBAC Association tables
user_role_association = Table(
    "user_role_association",
    Base.metadata,
    Column("user_id", String, ForeignKey("users.id"), primary_key=True),
    Column("role_id", String, ForeignKey("roles.id"), primary_key=True),
    Column("assigned_at", DateTime(timezone=True), server_default=func.now()),
    Column("assigned_by", String, ForeignKey("users.id"), nullable=True),
    Column("expires_at", DateTime(timezone=True), nullable=True),
)

role_permission_association = Table(
    "role_permission_association",
    Base.metadata,
    Column("role_id", String, ForeignKey("roles.id"), primary_key=True),
    Column("permission_id", String, ForeignKey("permissions.id"), primary_key=True),
)

user_workspace_association = Table(
    "user_workspace_association",
    Base.metadata,
    Column("user_id", String, ForeignKey("users.id"), primary_key=True),
    Column("workspace_id", String, ForeignKey("workspaces.id"), primary_key=True),
    Column("role_id", String, ForeignKey("roles.id")),
    Column("joined_at", DateTime(timezone=True), server_default=func.now()),
    Column("invited_by", String, ForeignKey("users.id"), nullable=True),
)

# User model
class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    role = Column(String, default="user")  # user, admin, etc.
    preferences = Column(JSON, nullable=True)
    
    # Relationships
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    conversations = relationship("Conversation", secondary=user_conversation_association, back_populates="users")
    messages = relationship("Message", back_populates="user")
    files = relationship("File", back_populates="user")
    
    # RBAC Relationships
    roles = relationship(
        "Role", 
        secondary=user_role_association, 
        back_populates="users",
        primaryjoin="User.id == user_role_association.c.user_id",
        secondaryjoin="Role.id == user_role_association.c.role_id"
    )
    workspaces = relationship(
        "Workspace", 
        secondary=user_workspace_association, 
        back_populates="members",
        primaryjoin="User.id == user_workspace_association.c.user_id",
        secondaryjoin="Workspace.id == user_workspace_association.c.workspace_id"
    )
    owned_workspaces = relationship("Workspace", back_populates="owner", foreign_keys="Workspace.owner_id")
    audit_logs = relationship("AuditLog", back_populates="user", foreign_keys="AuditLog.user_id")

# API Key model for authenticating API requests
class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(String, primary_key=True, default=generate_uuid)
    key = Column(String, unique=True, index=True)
    name = Column(String)
    user_id = Column(String, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", back_populates="api_keys")


# RBAC Models
class Role(Base):
    """Role model for RBAC system."""
    __tablename__ = "roles"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, unique=True, index=True)  # admin, user, manager, analyst, etc.
    display_name = Column(String)
    description = Column(Text, nullable=True)
    is_system = Column(Boolean, default=False)  # System roles cannot be deleted
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, ForeignKey("users.id"), nullable=True)
    
    # Role hierarchy
    parent_role_id = Column(String, ForeignKey("roles.id"), nullable=True)
    level = Column(Integer, default=0)  # Role hierarchy level
    
    # Relationships
    users = relationship(
        "User", 
        secondary=user_role_association, 
        back_populates="roles",
        primaryjoin="Role.id == user_role_association.c.role_id",
        secondaryjoin="User.id == user_role_association.c.user_id"
    )
    permissions = relationship("Permission", secondary=role_permission_association, back_populates="roles")
    parent_role = relationship("Role", remote_side=[id], backref="child_roles")
    creator = relationship("User", foreign_keys=[created_by])


class Permission(Base):
    """Permission model for granular access control."""
    __tablename__ = "permissions"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, unique=True, index=True)  # e.g., "conversations.create", "models.manage"
    display_name = Column(String)
    description = Column(Text, nullable=True)
    resource = Column(String, index=True)  # conversations, models, users, workspaces, etc.
    action = Column(String, index=True)  # create, read, update, delete, manage, execute
    scope = Column(String, default="workspace")  # global, workspace, own
    is_system = Column(Boolean, default=False)  # System permissions cannot be deleted
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    roles = relationship("Role", secondary=role_permission_association, back_populates="permissions")


class Workspace(Base):
    """Workspace model for team collaboration."""
    __tablename__ = "workspaces"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, index=True)
    display_name = Column(String)
    description = Column(Text, nullable=True)
    slug = Column(String, unique=True, index=True)  # URL-friendly workspace identifier
    
    # Workspace settings
    is_active = Column(Boolean, default=True)
    is_public = Column(Boolean, default=False)
    settings = Column(JSON, nullable=True)  # Workspace-specific settings
    
    # Ownership and billing
    owner_id = Column(String, ForeignKey("users.id"))
    plan = Column(String, default="free")  # free, pro, enterprise
    billing_settings = Column(JSON, nullable=True)
    
    # Usage limits and quotas
    usage_limits = Column(JSON, nullable=True)
    current_usage = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    owner = relationship("User", back_populates="owned_workspaces", foreign_keys=[owner_id])
    members = relationship(
        "User", 
        secondary=user_workspace_association, 
        back_populates="workspaces",
        primaryjoin="Workspace.id == user_workspace_association.c.workspace_id",
        secondaryjoin="User.id == user_workspace_association.c.user_id"
    )
    conversations = relationship("Conversation", back_populates="workspace")
    # pipelines = relationship("Pipeline", back_populates="workspace")  # Commented out due to import conflicts
    shared_credentials = relationship("WorkspaceCredential", back_populates="workspace")
    audit_logs = relationship("AuditLog", back_populates="workspace")


class WorkspaceCredential(Base):
    """Shared credentials for workspace members."""
    __tablename__ = "workspace_credentials"

    id = Column(String, primary_key=True, default=generate_uuid)
    workspace_id = Column(String, ForeignKey("workspaces.id"))
    provider_type = Column(String, index=True)
    credential_name = Column(String)
    encrypted_api_key = Column(Text)
    encrypted_data = Column(JSON, nullable=True)
    
    # Access control
    is_active = Column(Boolean, default=True)
    access_level = Column(String, default="read")  # read, write, admin
    allowed_roles = Column(JSON, nullable=True)  # Role IDs that can access this credential
    
    # Tracking
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(String, ForeignKey("users.id"))
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    workspace = relationship("Workspace", back_populates="shared_credentials")
    creator = relationship("User")


class AuditLog(Base):
    """Audit logging for compliance and security."""
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=generate_uuid)
    
    # Who, What, When, Where
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    action = Column(String, index=True)  # create, update, delete, access, etc.
    resource_type = Column(String, index=True)  # conversation, model, user, etc.
    resource_id = Column(String, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Context
    workspace_id = Column(String, ForeignKey("workspaces.id"), nullable=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    session_id = Column(String, nullable=True)
    
    # Details
    old_values = Column(JSON, nullable=True)  # Previous state
    new_values = Column(JSON, nullable=True)  # New state
    meta_data = Column(JSON, nullable=True)  # Additional context
    
    # Risk assessment
    risk_level = Column(String, default="low")  # low, medium, high, critical
    is_suspicious = Column(Boolean, default=False)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    workspace = relationship("Workspace", back_populates="audit_logs")


# Model represents an AI model (e.g., GPT-4, Claude, etc.)
class Model(Base):
    __tablename__ = "models"

    id = Column(String, primary_key=True)  # e.g., "gpt-4", "claude-3-opus-20240229"
    name = Column(String)
    provider = Column(String)  # OpenAI, Anthropic, etc.
    description = Column(Text, nullable=True)
    version = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    parameters = Column(JSON, nullable=True)  # Model-specific parameters
    capabilities = Column(JSON, nullable=True)  # What the model can do
    context_window = Column(Integer)  # Max token context window
    max_output_tokens = Column(Integer, nullable=True)
    pricing = Column(JSON, nullable=True)  # Cost per token
    size = Column(String, nullable=True)  # Size of the model (e.g., "3.8 GB")
    status = Column(String, default="inactive")  # Status: active, inactive, running
    is_local = Column(Boolean, default=True)  # Whether it's a local Ollama model
    model_metadata = Column("metadata", JSON, nullable=True)  # Additional metadata
    
    # Relationships
    tags = relationship("Tag", secondary=model_tag_association, back_populates="models")
    conversations = relationship("Conversation", back_populates="model")

# Tag model for categorizing models
class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String, nullable=True)
    
    # Relationships
    models = relationship("Model", secondary=model_tag_association, back_populates="tags")

# Conversation model
class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String, primary_key=True, default=generate_uuid)
    title = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    model_id = Column(String, ForeignKey("models.id"))
    system_prompt = Column(Text, nullable=True)
    meta_data = Column(JSON, nullable=True)  # Changed from metadata to avoid SQLAlchemy conflicts
    
    # Workspace integration
    workspace_id = Column(String, ForeignKey("workspaces.id"), nullable=True)
    
    # Relationships
    model = relationship("Model", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", order_by="Message.created_at", cascade="all, delete-orphan")
    users = relationship("User", secondary=user_conversation_association, back_populates="conversations")
    files = relationship("File", back_populates="conversation")
    threads = relationship("MessageThread", back_populates="conversation", cascade="all, delete-orphan")
    workspace = relationship("Workspace", back_populates="conversations")
    
    # Extended relationships for conversation management
    folders = relationship("ConversationFolder", secondary="conversation_folder_association", back_populates="conversations")
    shares = relationship("ConversationShare", cascade="all, delete-orphan")
    collaborators = relationship("ConversationCollaborator", cascade="all, delete-orphan")
    activities = relationship("ConversationActivity", cascade="all, delete-orphan")
    bookmarks = relationship("ConversationBookmark", cascade="all, delete-orphan")

# Message model
class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=generate_uuid)
    conversation_id = Column(String, ForeignKey("conversations.id"))
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    role = Column(String)  # "system", "user", "assistant"
    content = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    meta_data = Column(JSON, nullable=True)  # Changed from metadata to avoid SQLAlchemy conflicts
    tokens = Column(Integer, nullable=True)
    cost = Column(Float, nullable=True)
    parent_id = Column(String, ForeignKey("messages.id"), nullable=True)
    thread_id = Column(String, ForeignKey("message_threads.id"), nullable=True)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    user = relationship("User", back_populates="messages")
    files = relationship("MessageFile", back_populates="message", cascade="all, delete-orphan")
    parent = relationship("Message", remote_side=[id], backref="replies")
    thread = relationship("MessageThread", back_populates="messages")

# File model for storing uploaded files
class File(Base):
    __tablename__ = "files"

    id = Column(String, primary_key=True, default=generate_uuid)
    filename = Column(String)
    original_filename = Column(String)
    content_type = Column(String)
    size = Column(Integer)
    path = Column(String)  # Storage path
    user_id = Column(String, ForeignKey("users.id"))
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    meta_data = Column(JSON, nullable=True)  # Changed from metadata to avoid SQLAlchemy conflicts
    is_public = Column(Boolean, default=False)
    analyzed = Column(Boolean, default=False)
    analysis_result = Column(JSON, nullable=True)  # Results of AI analysis
    extracted_text = Column(Text, nullable=True)  # Text extracted from file
    
    # Relationships
    user = relationship("User", back_populates="files")
    conversation = relationship("Conversation", back_populates="files")
    message_files = relationship("MessageFile", back_populates="file", cascade="all, delete-orphan")

# MessageFile junction table to associate files with messages
class MessageFile(Base):
    __tablename__ = "message_files"

    message_id = Column(String, ForeignKey("messages.id"), primary_key=True)
    file_id = Column(String, ForeignKey("files.id"), primary_key=True)
    
    # Relationships
    message = relationship("Message", back_populates="files")
    file = relationship("File", back_populates="message_files")

# Message Thread model for organizing threaded conversations
class MessageThread(Base):
    __tablename__ = "message_threads"

    id = Column(String, primary_key=True, default=generate_uuid)
    conversation_id = Column(String, ForeignKey("conversations.id"))
    title = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    creator_id = Column(String, ForeignKey("users.id"), nullable=True)
    parent_thread_id = Column(String, ForeignKey("message_threads.id"), nullable=True)
    meta_data = Column(JSON, nullable=True)  # Changed from metadata to avoid SQLAlchemy conflicts
    
    # Relationships
    conversation = relationship("Conversation", back_populates="threads")
    messages = relationship("Message", back_populates="thread")
    creator = relationship("User")
    parent_thread = relationship("MessageThread", remote_side=[id], backref="child_threads")


# User Settings model for storing user preferences and provider credentials
class UserSettings(Base):
    __tablename__ = "user_settings"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), unique=True)
    provider_credentials = Column(JSON, nullable=True)  # Encrypted provider API keys
    preferences = Column(JSON, nullable=True)  # User preferences
    usage_limits = Column(JSON, nullable=True)  # Cost and usage limits
    notification_settings = Column(JSON, nullable=True)  # Notification preferences
    github_config = Column(JSON, nullable=True)  # Encrypted GitHub integration config
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", backref="settings")


# Provider Credentials model for secure storage of API credentials
class ProviderCredential(Base):
    __tablename__ = "provider_credentials"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"))
    provider_type = Column(String, index=True)  # openai, anthropic, google, etc.
    credential_name = Column(String)  # User-friendly name
    encrypted_api_key = Column(Text)  # Encrypted API key
    encrypted_data = Column(JSON, nullable=True)  # Other encrypted credential data
    is_active = Column(Boolean, default=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", backref="provider_credentials")


# Usage Tracking model for monitoring API usage and costs
class UsageRecord(Base):
    __tablename__ = "usage_records"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"))
    provider_type = Column(String, index=True)
    model_id = Column(String)
    operation = Column(String)  # text_generation, embeddings, image_generation, etc.
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    cost = Column(Float, default=0.0)
    pipeline_id = Column(String, nullable=True)  # Reference to pipeline (will be foreign key when pipelines are in same module)
    execution_id = Column(String, nullable=True)
    request_id = Column(String, nullable=True)
    response_time = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    meta_data = Column(JSON, nullable=True)  # Additional tracking data
    
    # Relationships
    user = relationship("User", backref="usage_records")


# Provider Health model for tracking provider status and performance
class ProviderHealth(Base):
    __tablename__ = "provider_health"

    id = Column(String, primary_key=True, default=generate_uuid)
    provider_type = Column(String, unique=True, index=True)
    is_available = Column(Boolean, default=True)
    last_check_at = Column(DateTime(timezone=True), server_default=func.now())
    response_time = Column(Float, nullable=True)  # Average response time in seconds
    error_rate = Column(Float, default=0.0)  # Error rate as percentage
    status_message = Column(Text, nullable=True)
    models_count = Column(Integer, default=0)
    capabilities = Column(JSON, nullable=True)
    pricing_data = Column(JSON, nullable=True)  # Cached pricing information
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


# Budget Alert model for cost monitoring and notifications
class BudgetAlert(Base):
    __tablename__ = "budget_alerts"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"))
    alert_name = Column(String)
    threshold_amount = Column(Float)  # Dollar amount threshold
    period = Column(String)  # daily, weekly, monthly
    provider_type = Column(String, nullable=True)  # Specific provider or all
    is_active = Column(Boolean, default=True)
    triggered_count = Column(Integer, default=0)
    last_triggered_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", backref="budget_alerts")


# Pipeline model is now in db/pipeline_models.py to avoid conflicts


# Workspace Invitation model for team onboarding
class WorkspaceInvitation(Base):
    """Workspace invitation model for team collaboration."""
    __tablename__ = "workspace_invitations"

    id = Column(String, primary_key=True, default=generate_uuid)
    workspace_id = Column(String, ForeignKey("workspaces.id"))
    email = Column(String, index=True)
    token = Column(String, unique=True, index=True)
    role = Column(String, default="user")
    message = Column(Text, nullable=True)
    
    # Invitation status
    status = Column(String, default="pending")  # pending, accepted, expired, cancelled
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Tracking
    invited_by = Column(String, ForeignKey("users.id"))
    accepted_by = Column(String, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    workspace = relationship("Workspace")
    inviter = relationship("User", foreign_keys=[invited_by])
    accepter = relationship("User", foreign_keys=[accepted_by])