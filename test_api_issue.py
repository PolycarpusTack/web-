import asyncio
import httpx
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

async def test_ollama():
    print("Testing Ollama connection...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:11434/api/tags")
            print(f"Ollama Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"Available models: {len(data.get('models', []))}")
                for model in data.get('models', [])[:3]:
                    print(f"  - {model['name']}")
    except Exception as e:
        print(f"Ollama Error: {e}")

async def test_database():
    print("\nTesting database connection...")
    try:
        engine = create_async_engine("sqlite+aiosqlite:///./web_plus.db", echo=True)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as session:
            result = await session.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = result.fetchall()
            print(f"Database tables: {len(tables)}")
            for table in tables:
                print(f"  - {table[0]}")
                
        await engine.dispose()
    except Exception as e:
        print(f"Database Error: {e}")

async def test_api():
    print("\nTesting API endpoint...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8002/api/models/available")
            print(f"API Status: {response.status_code}")
            if response.status_code != 200:
                print(f"API Response: {response.text}")
    except Exception as e:
        print(f"API Error: {e}")

async def main():
    await test_ollama()
    await test_database()
    await test_api()

if __name__ == "__main__":
    asyncio.run(main())
