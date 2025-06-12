from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL from environment or use default SQLite database
db_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web_plus.db")
DATABASE_URL = os.getenv("WEBPLUS_DATABASE_URL", f"sqlite+aiosqlite:///{db_file}")

# Create async engine for modern SQLAlchemy style
engine = create_async_engine(
    DATABASE_URL, 
    echo=False,
    future=True
)

# Create sessionmaker for creating database sessions
async_session_maker = sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False,
    autoflush=False
)

# Create base class for declarative models
Base = declarative_base()

# Dependency for getting the database session
async def get_db():
    """
    Dependency function that yields db sessions
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# For synchronous use (e.g., in migrations)
SYNC_DATABASE_URL = DATABASE_URL.replace("sqlite+aiosqlite://", "sqlite:///")
sync_engine = create_engine(SYNC_DATABASE_URL, echo=False)
sync_session_maker = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

# Aliases for backward compatibility
async_engine = engine

# Additional session getters
async def get_async_session():
    """Get an async database session."""
    async with async_session_maker() as session:
        yield session

def get_sync_db():
    """Get a synchronous database session."""
    db = sync_session_maker()
    try:
        yield db
    finally:
        db.close()

# Database initialization functions
async def init_async_db():
    """Initialize the async database."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def close_async_db():
    """Close the async database engine."""
    await engine.dispose()
