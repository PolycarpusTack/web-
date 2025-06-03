"""
Simple test script to verify workspace functionality works.
"""

import asyncio
from db.database import async_session_maker
from db.crud import (
    create_user, get_user_by_username, create_workspace, 
    get_user_workspaces, assign_role_to_user, get_role_by_name
)
from auth.password import hash_password

async def test_workspace_functionality():
    """Test basic workspace operations."""
    print("🧪 Testing workspace functionality...")
    
    async with async_session_maker() as db:
        # Create a test user if not exists
        test_user = await get_user_by_username(db, "testuser")
        if not test_user:
            test_user = await create_user(
                db=db,
                username="testuser",
                email="test@example.com",
                hashed_password=hash_password("testpass123"),
                full_name="Test User"
            )
            print(f"✓ Created test user: {test_user.username}")
        else:
            print(f"✓ Using existing test user: {test_user.username}")
        
        # Assign user role
        user_role = await get_role_by_name(db, "user")
        if user_role:
            await assign_role_to_user(db, test_user.id, user_role.id)
            print(f"✓ Assigned user role to test user")
        
        # Create a test workspace
        try:
            test_workspace = await create_workspace(
                db=db,
                name="test-workspace",
                display_name="Test Workspace",
                slug="test-workspace",
                owner_id=test_user.id,
                description="A test workspace for development",
                is_public=False,
                plan="free"
            )
            print(f"✓ Created test workspace: {test_workspace.display_name}")
        except Exception as e:
            print(f"! Workspace might already exist: {e}")
        
        # List user workspaces
        workspaces = await get_user_workspaces(db, test_user.id)
        print(f"✓ User has access to {len(workspaces)} workspace(s)")
        
        for workspace in workspaces:
            print(f"  - {workspace.display_name} ({workspace.plan})")
        
        print("\n✅ Workspace functionality test completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_workspace_functionality())