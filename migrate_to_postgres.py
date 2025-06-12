#!/usr/bin/env python
"""
Migrate Web+ from SQLite to PostgreSQL
"""
import os
import sys
import asyncio
import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine
import asyncpg

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
POSTGRES_CONFIG = {
    "user": "postgres",
    "password": "Th1s1s4Work",
    "host": "localhost",
    "port": 5433,
    "database": "webplus"
}

async def create_postgres_database():
    """Create PostgreSQL database if it doesn't exist"""
    try:
        # Connect to default postgres database
        conn = await asyncpg.connect(
            user=POSTGRES_CONFIG["user"],
            password=POSTGRES_CONFIG["password"],
            host=POSTGRES_CONFIG["host"],
            port=POSTGRES_CONFIG["port"],
            database="postgres"
        )
        
        # Check if database exists
        exists = await conn.fetchval(
            "SELECT EXISTS(SELECT 1 FROM pg_database WHERE datname = $1)",
            POSTGRES_CONFIG["database"]
        )
        
        if not exists:
            # Create database
            await conn.execute(f'CREATE DATABASE {POSTGRES_CONFIG["database"]}')
            logger.info(f"Created database: {POSTGRES_CONFIG['database']}")
        else:
            logger.info(f"Database already exists: {POSTGRES_CONFIG['database']}")
            
        await conn.close()
        
    except asyncpg.InvalidCatalogNameError:
        # User doesn't exist, need to create it first
        logger.error("PostgreSQL user doesn't exist. Please create it manually:")
        logger.error(f"CREATE USER {POSTGRES_CONFIG['user']} WITH PASSWORD '{POSTGRES_CONFIG['password']}';")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error creating database: {e}")
        sys.exit(1)

async def update_env_file():
    """Update .env file with PostgreSQL configuration"""
    backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "apps", "backend")
    env_file = os.path.join(backend_dir, ".env")
    
    # Read current .env
    with open(env_file, 'r') as f:
        lines = f.readlines()
    
    # Update database URL
    updated_lines = []
    for line in lines:
        if line.startswith("WEBPLUS_DATABASE_URL="):
            updated_lines.append(f"WEBPLUS_DATABASE_URL=postgresql+asyncpg://{POSTGRES_CONFIG['user']}:{POSTGRES_CONFIG['password']}@{POSTGRES_CONFIG['host']}:{POSTGRES_CONFIG['port']}/{POSTGRES_CONFIG['database']}\n")
        else:
            updated_lines.append(line)
    
    # Write back
    with open(env_file, 'w') as f:
        f.writelines(updated_lines)
    
    logger.info("Updated .env file with PostgreSQL configuration")

async def initialize_database():
    """Initialize database schema"""
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "apps", "backend"))
    
    from db.database import init_async_db
    from db.init_db import init_db
    from db.database import async_engine
    
    # Create tables
    await init_async_db()
    logger.info("Created database schema")
    
    # Initialize with default data
    await init_db()
    logger.info("Initialized database with default data")

async def main():
    logger.info("Starting migration to PostgreSQL...")
    
    # Step 1: Create PostgreSQL database
    await create_postgres_database()
    
    # Step 2: Update .env file
    await update_env_file()
    
    # Step 3: Initialize database
    await initialize_database()
    
    logger.info("Migration completed successfully!")
    logger.info("You can now start the application with PostgreSQL")

if __name__ == "__main__":
    asyncio.run(main())
