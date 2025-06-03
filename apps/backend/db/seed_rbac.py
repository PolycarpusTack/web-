"""
Seed script for RBAC (Role-Based Access Control) system.
Creates default roles and permissions for Web+ enterprise features.
"""

import asyncio
import sys
import os

# Add the parent directory to the path so we can import from db
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from db.database import async_session_maker
from db.crud import (
    create_role, create_permission, assign_permission_to_role,
    get_role_by_name, get_permission_by_name
)

# Default permissions for Web+ enterprise features
DEFAULT_PERMISSIONS = [
    # Conversation permissions
    {"name": "conversations.create", "display_name": "Create Conversations", "resource": "conversations", "action": "create", "scope": "workspace"},
    {"name": "conversations.read", "display_name": "Read Conversations", "resource": "conversations", "action": "read", "scope": "workspace"},
    {"name": "conversations.update", "display_name": "Update Conversations", "resource": "conversations", "action": "update", "scope": "own"},
    {"name": "conversations.delete", "display_name": "Delete Conversations", "resource": "conversations", "action": "delete", "scope": "own"},
    {"name": "conversations.manage", "display_name": "Manage All Conversations", "resource": "conversations", "action": "manage", "scope": "workspace"},
    
    # Model permissions
    {"name": "models.read", "display_name": "Read Models", "resource": "models", "action": "read", "scope": "workspace"},
    {"name": "models.use", "display_name": "Use Models", "resource": "models", "action": "use", "scope": "workspace"},
    {"name": "models.manage", "display_name": "Manage Models", "resource": "models", "action": "manage", "scope": "workspace"},
    
    # Pipeline permissions
    {"name": "pipelines.create", "display_name": "Create Pipelines", "resource": "pipelines", "action": "create", "scope": "workspace"},
    {"name": "pipelines.read", "display_name": "Read Pipelines", "resource": "pipelines", "action": "read", "scope": "workspace"},
    {"name": "pipelines.update", "display_name": "Update Pipelines", "resource": "pipelines", "action": "update", "scope": "own"},
    {"name": "pipelines.delete", "display_name": "Delete Pipelines", "resource": "pipelines", "action": "delete", "scope": "own"},
    {"name": "pipelines.execute", "display_name": "Execute Pipelines", "resource": "pipelines", "action": "execute", "scope": "workspace"},
    {"name": "pipelines.manage", "display_name": "Manage All Pipelines", "resource": "pipelines", "action": "manage", "scope": "workspace"},
    
    # User permissions
    {"name": "users.read", "display_name": "Read Users", "resource": "users", "action": "read", "scope": "workspace"},
    {"name": "users.invite", "display_name": "Invite Users", "resource": "users", "action": "invite", "scope": "workspace"},
    {"name": "users.manage", "display_name": "Manage Users", "resource": "users", "action": "manage", "scope": "workspace"},
    
    # Workspace permissions
    {"name": "workspaces.read", "display_name": "Read Workspace", "resource": "workspaces", "action": "read", "scope": "workspace"},
    {"name": "workspaces.update", "display_name": "Update Workspace", "resource": "workspaces", "action": "update", "scope": "workspace"},
    {"name": "workspaces.manage", "display_name": "Manage Workspace", "resource": "workspaces", "action": "manage", "scope": "workspace"},
    {"name": "workspaces.delete", "display_name": "Delete Workspace", "resource": "workspaces", "action": "delete", "scope": "workspace"},
    
    # File permissions
    {"name": "files.upload", "display_name": "Upload Files", "resource": "files", "action": "upload", "scope": "workspace"},
    {"name": "files.read", "display_name": "Read Files", "resource": "files", "action": "read", "scope": "workspace"},
    {"name": "files.delete", "display_name": "Delete Files", "resource": "files", "action": "delete", "scope": "own"},
    {"name": "files.manage", "display_name": "Manage All Files", "resource": "files", "action": "manage", "scope": "workspace"},
    
    # Provider credentials permissions
    {"name": "credentials.read", "display_name": "Read Credentials", "resource": "credentials", "action": "read", "scope": "workspace"},
    {"name": "credentials.create", "display_name": "Create Credentials", "resource": "credentials", "action": "create", "scope": "workspace"},
    {"name": "credentials.update", "display_name": "Update Credentials", "resource": "credentials", "action": "update", "scope": "workspace"},
    {"name": "credentials.delete", "display_name": "Delete Credentials", "resource": "credentials", "action": "delete", "scope": "workspace"},
    {"name": "credentials.manage", "display_name": "Manage All Credentials", "resource": "credentials", "action": "manage", "scope": "workspace"},
    
    # Analytics and reporting permissions
    {"name": "analytics.read", "display_name": "Read Analytics", "resource": "analytics", "action": "read", "scope": "workspace"},
    {"name": "analytics.export", "display_name": "Export Analytics", "resource": "analytics", "action": "export", "scope": "workspace"},
    
    # Audit permissions
    {"name": "audit.read", "display_name": "Read Audit Logs", "resource": "audit", "action": "read", "scope": "workspace"},
    {"name": "audit.export", "display_name": "Export Audit Logs", "resource": "audit", "action": "export", "scope": "workspace"},
    
    # System admin permissions (global scope)
    {"name": "system.users.manage", "display_name": "Manage System Users", "resource": "users", "action": "manage", "scope": "global"},
    {"name": "system.workspaces.manage", "display_name": "Manage All Workspaces", "resource": "workspaces", "action": "manage", "scope": "global"},
    {"name": "system.providers.manage", "display_name": "Manage Providers", "resource": "providers", "action": "manage", "scope": "global"},
    {"name": "system.settings.manage", "display_name": "Manage System Settings", "resource": "settings", "action": "manage", "scope": "global"},
    {"name": "system.audit.read", "display_name": "Read All Audit Logs", "resource": "audit", "action": "read", "scope": "global"},
]

# Default roles with their permissions
DEFAULT_ROLES = [
    {
        "name": "viewer",
        "display_name": "Viewer",
        "description": "Can view conversations, models, and pipelines but cannot modify anything",
        "is_system": True,
        "level": 0,
        "permissions": [
            "conversations.read",
            "models.read",
            "pipelines.read",
            "files.read",
            "workspaces.read",
            "analytics.read"
        ]
    },
    {
        "name": "user",
        "display_name": "User",
        "description": "Standard user with basic permissions to create and manage own content",
        "is_system": True,
        "level": 1,
        "permissions": [
            "conversations.create", "conversations.read", "conversations.update", "conversations.delete",
            "models.read", "models.use",
            "pipelines.create", "pipelines.read", "pipelines.update", "pipelines.delete", "pipelines.execute",
            "files.upload", "files.read", "files.delete",
            "workspaces.read",
            "analytics.read"
        ]
    },
    {
        "name": "collaborator",
        "display_name": "Collaborator",
        "description": "Can collaborate on shared content and access team resources",
        "is_system": True,
        "level": 2,
        "permissions": [
            "conversations.create", "conversations.read", "conversations.update", "conversations.delete", "conversations.manage",
            "models.read", "models.use",
            "pipelines.create", "pipelines.read", "pipelines.update", "pipelines.delete", "pipelines.execute", "pipelines.manage",
            "files.upload", "files.read", "files.delete", "files.manage",
            "workspaces.read",
            "credentials.read",
            "analytics.read", "analytics.export"
        ]
    },
    {
        "name": "manager",
        "display_name": "Manager",
        "description": "Can manage team members and workspace resources",
        "is_system": True,
        "level": 3,
        "permissions": [
            "conversations.create", "conversations.read", "conversations.update", "conversations.delete", "conversations.manage",
            "models.read", "models.use", "models.manage",
            "pipelines.create", "pipelines.read", "pipelines.update", "pipelines.delete", "pipelines.execute", "pipelines.manage",
            "files.upload", "files.read", "files.delete", "files.manage",
            "users.read", "users.invite",
            "workspaces.read", "workspaces.update",
            "credentials.read", "credentials.create", "credentials.update", "credentials.delete",
            "analytics.read", "analytics.export",
            "audit.read"
        ]
    },
    {
        "name": "admin",
        "display_name": "Administrator",
        "description": "Full workspace administrator with all permissions",
        "is_system": True,
        "level": 4,
        "permissions": [
            "conversations.create", "conversations.read", "conversations.update", "conversations.delete", "conversations.manage",
            "models.read", "models.use", "models.manage",
            "pipelines.create", "pipelines.read", "pipelines.update", "pipelines.delete", "pipelines.execute", "pipelines.manage",
            "files.upload", "files.read", "files.delete", "files.manage",
            "users.read", "users.invite", "users.manage",
            "workspaces.read", "workspaces.update", "workspaces.manage", "workspaces.delete",
            "credentials.read", "credentials.create", "credentials.update", "credentials.delete", "credentials.manage",
            "analytics.read", "analytics.export",
            "audit.read", "audit.export"
        ]
    },
    {
        "name": "system_admin",
        "display_name": "System Administrator",
        "description": "Global system administrator with all system-level permissions",
        "is_system": True,
        "level": 5,
        "permissions": [
            # All regular permissions
            "conversations.create", "conversations.read", "conversations.update", "conversations.delete", "conversations.manage",
            "models.read", "models.use", "models.manage",
            "pipelines.create", "pipelines.read", "pipelines.update", "pipelines.delete", "pipelines.execute", "pipelines.manage",
            "files.upload", "files.read", "files.delete", "files.manage",
            "users.read", "users.invite", "users.manage",
            "workspaces.read", "workspaces.update", "workspaces.manage", "workspaces.delete",
            "credentials.read", "credentials.create", "credentials.update", "credentials.delete", "credentials.manage",
            "analytics.read", "analytics.export",
            "audit.read", "audit.export",
            # System-level permissions
            "system.users.manage",
            "system.workspaces.manage",
            "system.providers.manage",
            "system.settings.manage",
            "system.audit.read"
        ]
    }
]


async def seed_permissions(db: AsyncSession):
    """Create default permissions."""
    print("Creating default permissions...")
    
    for perm_data in DEFAULT_PERMISSIONS:
        existing = await get_permission_by_name(db, perm_data["name"])
        if not existing:
            permission = await create_permission(
                db=db,
                name=perm_data["name"],
                display_name=perm_data["display_name"],
                description=perm_data.get("description"),
                resource=perm_data["resource"],
                action=perm_data["action"],
                scope=perm_data["scope"],
                is_system=True
            )
            print(f"  ✓ Created permission: {permission.name}")
        else:
            print(f"  - Permission already exists: {perm_data['name']}")


async def seed_roles(db: AsyncSession):
    """Create default roles and assign permissions."""
    print("Creating default roles...")
    
    for role_data in DEFAULT_ROLES:
        existing = await get_role_by_name(db, role_data["name"])
        if not existing:
            role = await create_role(
                db=db,
                name=role_data["name"],
                display_name=role_data["display_name"],
                description=role_data["description"],
                is_system=role_data["is_system"]
            )
            print(f"  ✓ Created role: {role.name}")
            
            # Assign permissions to role
            print(f"    Assigning {len(role_data['permissions'])} permissions...")
            for perm_name in role_data["permissions"]:
                permission = await get_permission_by_name(db, perm_name)
                if permission:
                    success = await assign_permission_to_role(db, role.id, permission.id)
                    if success:
                        print(f"      ✓ Assigned permission: {perm_name}")
                    else:
                        print(f"      - Permission already assigned: {perm_name}")
                else:
                    print(f"      ✗ Permission not found: {perm_name}")
        else:
            print(f"  - Role already exists: {role_data['name']}")


async def seed_rbac():
    """Main seeding function."""
    print("🌱 Seeding RBAC system...")
    
    async with async_session_maker() as db:
        await seed_permissions(db)
        print()
        await seed_roles(db)
    
    print("\n✅ RBAC seeding completed!")


if __name__ == "__main__":
    asyncio.run(seed_rbac())