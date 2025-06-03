import asyncio
import os
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from .database import engine, async_session_maker, Base
from .init_db import init_db

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def reset_db() -> None:
    """Drop all tables and reinitialize the database."""
    # Drop all tables
    async with engine.begin() as conn:
        logger.info("Dropping all tables...")
        await conn.run_sync(Base.metadata.drop_all)
    
    # Reinitialize the database
    await init_db()

if __name__ == "__main__":
    """Run the database reset script."""
    asyncio.run(reset_db())
    logger.info("Database reset complete!")