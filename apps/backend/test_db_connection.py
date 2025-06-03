#!/usr/bin/env python3
"""
Test script to verify database connections.
Run this to ensure SQLite and async support are working correctly.
"""
import asyncio
import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from db.database import (
    test_async_connection,
    test_sync_connection,
    init_async_db,
    init_sync_db,
    close_async_db,
    close_sync_db,
    IS_SQLITE,
    DB_FILE,
)


async def main():
    """Test database connections and initialization."""
    print("=" * 60)
    print("Database Connection Test")
    print("=" * 60)
    
    # Display configuration
    print(f"\nConfiguration:")
    print(f"  Database Type: {'SQLite' if IS_SQLITE else 'PostgreSQL'}")
    if IS_SQLITE:
        print(f"  Database File: {DB_FILE}")
        print(f"  File Exists: {os.path.exists(DB_FILE)}")
    print()
    
    # Test sync connection
    print("Testing synchronous connection...")
    sync_result = test_sync_connection()
    print(f"  Result: {'✅ Success' if sync_result else '❌ Failed'}")
    
    # Test async connection
    print("\nTesting asynchronous connection...")
    async_result = await test_async_connection()
    print(f"  Result: {'✅ Success' if async_result else '❌ Failed'}")
    
    # Initialize database tables
    if sync_result and async_result:
        print("\nInitializing database tables...")
        try:
            # Try async initialization first
            await init_async_db()
            print("  ✅ Tables created successfully (async)")
        except Exception as e:
            print(f"  ❌ Async initialization failed: {e}")
            # Fallback to sync initialization
            try:
                init_sync_db()
                print("  ✅ Tables created successfully (sync)")
            except Exception as e2:
                print(f"  ❌ Sync initialization also failed: {e2}")
    
    # Cleanup
    print("\nCleaning up...")
    await close_async_db()
    close_sync_db()
    print("  ✅ Connections closed")
    
    # Summary
    print("\n" + "=" * 60)
    if sync_result and async_result:
        print("✅ All tests passed! Database is working correctly.")
    else:
        print("❌ Some tests failed. Please check the error messages above.")
        sys.exit(1)


if __name__ == "__main__":
    # Check Python version
    if sys.version_info < (3, 9):
        print(f"❌ Python 3.9+ required, but you have {sys.version}")
        sys.exit(1)
    
    # Run the tests
    asyncio.run(main())