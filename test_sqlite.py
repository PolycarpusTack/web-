
"""
A simple test script to check if SQLAlchemy can connect to SQLite.
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

async def test_connection():
    # Create async engine with SQLite
    DATABASE_URL = "sqlite+aiosqlite:///./test.db"
    engine = create_async_engine(
        DATABASE_URL, 
        echo=True,
        future=True
    )
    
    # Create a session
    async_session_maker = sessionmaker(
        engine, 
        class_=AsyncSession, 
        expire_on_commit=False,
        autoflush=False
    )
    
    # Create a base for models
    Base = declarative_base()
    
    # Define a simple model
    from sqlalchemy import Column, Integer, String
    
    class User(Base):
        __tablename__ = "users"
        id = Column(Integer, primary_key=True)
        name = Column(String)
    
    # Create tables
    async with engine.begin() as conn:
        print("Creating tables...")
        await conn.run_sync(Base.metadata.create_all)
    
    print("Test completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_connection())
