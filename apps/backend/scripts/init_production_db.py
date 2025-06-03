#!/usr/bin/env python3
"""
Initialize production database (PostgreSQL).
This script creates the database, runs migrations, and optionally seeds initial data.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
import asyncpg
from core.config import settings
from db.seed_data import seed_database
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_database_if_not_exists():
    """Create PostgreSQL database if it doesn't exist."""
    if settings.is_sqlite:
        logger.info("Using SQLite, skipping database creation")
        return
    
    if not settings.postgres_server:
        logger.error("PostgreSQL server not configured")
        return
    
    # Connect to PostgreSQL server (not specific database)
    conn_str = f"postgresql://{settings.postgres_user}:{settings.postgres_password}@{settings.postgres_server}:{settings.postgres_port}/postgres"
    
    try:
        conn = await asyncpg.connect(conn_str)
        
        # Check if database exists
        exists = await conn.fetchval(
            "SELECT EXISTS(SELECT datname FROM pg_database WHERE datname = $1)",
            settings.postgres_db or "webplus"
        )
        
        if not exists:
            # Create database
            await conn.execute(f'CREATE DATABASE "{settings.postgres_db or "webplus"}"')
            logger.info(f"Created database: {settings.postgres_db or 'webplus'}")
        else:
            logger.info(f"Database already exists: {settings.postgres_db or 'webplus'}")
        
        await conn.close()
        
    except Exception as e:
        logger.error(f"Error creating database: {e}")
        raise


async def verify_connection():
    """Verify database connection."""
    try:
        engine = create_async_engine(settings.database_url, echo=False)
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            logger.info("Database connection verified")
        await engine.dispose()
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False


def run_migrations():
    """Run Alembic migrations."""
    try:
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
        logger.info("Migrations completed successfully")
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise


async def init_production_database(seed_data: bool = False):
    """Initialize production database."""
    logger.info(f"Initializing database: {settings.database_url}")
    
    # Step 1: Create database if using PostgreSQL
    if settings.is_postgresql:
        await create_database_if_not_exists()
    
    # Step 2: Verify connection
    if not await verify_connection():
        logger.error("Cannot connect to database")
        sys.exit(1)
    
    # Step 3: Run migrations
    logger.info("Running database migrations...")
    run_migrations()
    
    # Step 4: Seed data if requested
    if seed_data:
        logger.info("Seeding database...")
        result = await seed_database(environment="production", force=False)
        if result.get("success"):
            logger.info("Database seeding completed")
        else:
            logger.warning("Database seeding failed or skipped")
    
    logger.info("Database initialization complete!")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Initialize production database")
    parser.add_argument(
        "--seed",
        action="store_true",
        help="Seed the database with initial data"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-initialization (dangerous!)"
    )
    
    args = parser.parse_args()
    
    if args.force:
        response = input("WARNING: This will reset the database. Are you sure? (yes/no): ")
        if response.lower() != "yes":
            print("Aborted")
            sys.exit(0)
    
    asyncio.run(init_production_database(seed_data=args.seed))