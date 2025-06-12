"""
Minimal test to isolate the models endpoint issue
"""
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "apps", "backend"))

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import httpx

async def test_direct():
    print("Testing direct Ollama connection...")
    
    # Test Ollama directly
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:11434/api/tags")
            print(f"Ollama response: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"Found {len(data.get('models', []))} models in Ollama")
    except Exception as e:
        print(f"Ollama error: {e}")
    
    # Test database connection
    print("\nTesting database connection...")
    try:
        engine = create_async_engine(
            "postgresql+asyncpg://postgres:Th1s1s4Work@localhost:5433/webplus",
            echo=False
        )
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as session:
            from sqlalchemy import text
            result = await session.execute(text("SELECT COUNT(*) FROM models"))
            count = result.scalar()
            print(f"Found {count} models in database")
            
        await engine.dispose()
    except Exception as e:
        print(f"Database error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_direct())
