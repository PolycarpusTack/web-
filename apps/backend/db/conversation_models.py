"""
Extended conversation models for folders, sharing, and collaboration.
"""
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Text, JSON, Float, Table, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from datetime import datetime
import enum
from .database import Base

def generate_uuid():
    return str(uuid.uuid4())

# Association tables
conversation_folder_association = Table(
    "conversation_folder_association",
    Base.metadata,
    Column("conversation_id", String, ForeignKey("conversations.id"), primary_key=True),
    Column("folder_id", String, ForeignKey("conversation_folders.id"), primary_key=True),
)

conversation_share_association = Table(
    "conversation_share_association", 
    Base.metadata,
    Column("conversation_id", String, ForeignKey("conversations.id"), primary_key=True),
    Column("share_id", String, ForeignKey("conversation_shares.id"), primary_key=True),
)

folder_permission_association = Table(
    "folder_permission_association",
    Base.metadata,
    Column("folder_id", String, ForeignKey("conversation_folders.id"), primary_key=True),
    Column("user_id", String, ForeignKey("users.id"), primary_key=True),
    Column("permission_level", String, default="read"),  # read, write, admin
)

class PermissionLevel(enum.Enum):
    READ = "read"
    WRITE = "write" 
    ADMIN = "admin"

class ShareType(enum.Enum):
    PRIVATE = "private"
    LINK = "link"
    PUBLIC = "public"
    TEAM = "team"

class ConversationFolder(Base):
    """Folders for organizing conversations."""
    __tablename__ = "conversation_folders"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    color = Column(String, nullable=True)  # Hex color for UI
    icon = Column(String, nullable=True)  # Icon name for UI
    owner_id = Column(String, ForeignKey("users.id"), nullable=False)
    parent_folder_id = Column(String, ForeignKey("conversation_folders.id"), nullable=True)
    is_system = Column(Boolean, default=False)  # System folders like "Favorites", "Archive"
    is_shared = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    meta_data = Column(JSON, nullable=True)
    
    # Relationships
    owner = relationship("User")
    parent_folder = relationship("ConversationFolder", remote_side=[id], backref="sub_folders")
    conversations = relationship("Conversation", secondary=conversation_folder_association, back_populates="folders")
    permissions = relationship("User", secondary=folder_permission_association)

class ConversationShare(Base):
    """Sharing settings for conversations."""
    __tablename__ = "conversation_shares"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False)
    share_type = Column(Enum(ShareType), default=ShareType.PRIVATE)
    share_token = Column(String, unique=True, index=True, nullable=True)  # For link sharing
    shared_by_id = Column(String, ForeignKey("users.id"), nullable=False)
    shared_with_id = Column(String, ForeignKey("users.id"), nullable=True)  # For direct user sharing
    team_id = Column(String, nullable=True)  # For team sharing
    permission_level = Column(Enum(PermissionLevel), default=PermissionLevel.READ)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
    access_count = Column(Integer, default=0)
    last_accessed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    meta_data = Column(JSON, nullable=True)
    
    # Relationships
    conversation = relationship("Conversation")
    shared_by = relationship("User", foreign_keys=[shared_by_id])
    shared_with = relationship("User", foreign_keys=[shared_with_id])

class ConversationCollaborator(Base):
    """Collaborators with specific permissions on conversations."""
    __tablename__ = "conversation_collaborators"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    permission_level = Column(Enum(PermissionLevel), default=PermissionLevel.READ)
    invited_by_id = Column(String, ForeignKey("users.id"), nullable=False)
    invited_at = Column(DateTime(timezone=True), server_default=func.now())
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
    last_activity_at = Column(DateTime(timezone=True), nullable=True)
    meta_data = Column(JSON, nullable=True)
    
    # Relationships
    conversation = relationship("Conversation")
    user = relationship("User", foreign_keys=[user_id])
    invited_by = relationship("User", foreign_keys=[invited_by_id])

class ConversationActivity(Base):
    """Activity log for conversations."""
    __tablename__ = "conversation_activities"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    activity_type = Column(String, nullable=False)  # created, updated, shared, message_added, etc.
    description = Column(Text, nullable=True)
    details = Column(JSON, nullable=True)  # Structured activity data
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    
    # Relationships
    conversation = relationship("Conversation")
    user = relationship("User")

class ConversationTemplate(Base):
    """Templates for creating conversations with predefined settings."""
    __tablename__ = "conversation_templates"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    creator_id = Column(String, ForeignKey("users.id"), nullable=False)
    model_id = Column(String, ForeignKey("models.id"), nullable=False)
    system_prompt = Column(Text, nullable=True)
    initial_messages = Column(JSON, nullable=True)  # Pre-configured messages
    settings = Column(JSON, nullable=True)  # Temperature, max_tokens, etc.
    tags = Column(JSON, nullable=True)  # Categories/tags for templates
    is_public = Column(Boolean, default=False)
    is_featured = Column(Boolean, default=False)
    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    creator = relationship("User")
    model = relationship("Model")

class ConversationBookmark(Base):
    """User bookmarks for quick access to conversations."""
    __tablename__ = "conversation_bookmarks"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False)
    note = Column(Text, nullable=True)  # User's personal note about the bookmark
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User")
    conversation = relationship("Conversation")