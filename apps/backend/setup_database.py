#!/usr/bin/env python3
"""
Simple database setup script for Web+
Wrapper around the comprehensive init_database.py script
"""
import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db.init_database import DatabaseManager


async def quick_setup():
    """Quick database setup for development."""
    print("🚀 Web+ Database Quick Setup")
    print("=" * 50)
    
    db_manager = DatabaseManager()
    
    # Check current status
    print("\n📊 Checking database status...")
    status = await db_manager.get_database_status()
    
    print(f"   Database Type: {status['database_type']}")
    print(f"   Connection: {'✅' if status['connection_ok'] else '❌'}")
    
    if not status['connection_ok']:
        print("\n❌ Cannot connect to database. Please check your configuration.")
        return False
    
    # Check if we need to initialize
    tables_exist = any(status.get('tables', {}).values())
    
    if tables_exist:
        print("\n📋 Database tables already exist.")
        
        # Check record counts
        counts = status.get('record_counts', {})
        if counts:
            print("   Current data:")
            for table, count in counts.items():
                print(f"     {table}: {count} records")
        
        # Ask if user wants to add more seed data
        response = input("\n🌱 Add additional seed data? (y/N): ").strip().lower()
        if response == 'y':
            print("\n🌱 Adding seed data...")
            success = await db_manager.seed_database()
            if success:
                print("✅ Seed data added successfully!")
            else:
                print("❌ Failed to add seed data.")
                return False
        else:
            print("✅ Database is ready to use!")
    else:
        print("\n🏗️  Initializing database...")
        
        # Create tables
        print("   Creating tables...")
        success = await db_manager.create_tables()
        if not success:
            print("❌ Failed to create tables.")
            return False
        
        # Add seed data
        print("   Adding seed data...")
        success = await db_manager.seed_database()
        if not success:
            print("❌ Failed to add seed data.")
            return False
        
        print("✅ Database initialized successfully!")
    
    # Show final status
    print("\n📊 Final database status:")
    final_status = await db_manager.get_database_status()
    counts = final_status.get('record_counts', {})
    for table, count in counts.items():
        print(f"   {table}: {count} records")
    
    # Show admin credentials
    print("\n🔑 Admin Credentials:")
    print("   Username: admin")
    print("   Email: admin@webplus.local")
    print("   Password: webplus123")
    print("   (Change these in production!)")
    
    return True


async def main():
    """Main entry point."""
    try:
        success = await quick_setup()
        if success:
            print("\n🎉 Database setup complete! You can now start the Web+ server.")
            return 0
        else:
            print("\n💥 Database setup failed. Check the logs for details.")
            return 1
    except KeyboardInterrupt:
        print("\n⛔ Setup cancelled by user.")
        return 1
    except Exception as e:
        print(f"\n💥 Setup failed with error: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)