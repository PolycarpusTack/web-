#!/usr/bin/env python
"""
Initialize Web+ with existing PostgreSQL database
"""
import os
import sys
import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine

# Add backend to Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "apps", "backend"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_connection():
    """Test PostgreSQL connection"""
    try:
        engine = create_async_engine(
            "postgresql+asyncpg://postgres:Th1s1s4Work@localhost:5433/webplus",
            echo=True
        )
        
        async with engine.begin() as conn:
            from sqlalchemy import text
            result = await conn.execute(text("SELECT version()"))
            version = result.scalar()
            logger.info(f"Connected to PostgreSQL: {version}")
            
        await engine.dispose()
        return True
    except Exception as e:
        logger.error(f"Failed to connect to PostgreSQL: {e}")
        return False

async def initialize_database():
    """Initialize database schema and data"""
    from db.database import init_async_db
    from db.init_db import init_db
    
    try:
        # Create tables
        logger.info("Creating database schema...")
        await init_async_db()
        logger.info("Database schema created successfully")
        
        # Initialize with default data
        logger.info("Initializing default data...")
        await init_db()
        logger.info("Default data initialized successfully")
        
        return True
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return False

async def main():
    logger.info("Initializing Web+ with PostgreSQL...")
    
    # Test connection
    if not await test_connection():
        logger.error("Cannot connect to PostgreSQL. Please check:")
        logger.error("- PostgreSQL is running on port 5433")
        logger.error("- Database 'webplus' exists")
        logger.error("- Credentials are correct")
        sys.exit(1)
    
    # Initialize database
    if await initialize_database():
        logger.info("✅ Web+ is ready to use with PostgreSQL!")
        logger.info("Start the application with:")
        logger.info("  Backend:  cd apps/backend && python -m uvicorn main:app --host 0.0.0.0 --port 8002")
        logger.info("  Frontend: cd apps/frontend && npm run dev")
    else:
        logger.error("Failed to initialize database")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
