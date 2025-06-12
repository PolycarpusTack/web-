import asyncio
import asyncpg

async def test():
    try:
        conn = await asyncpg.connect(
            host='localhost',
            port=5433,
            user='postgres',
            password='Th1s1s4Work',
            database='webplus'
        )
        version = await conn.fetchval('SELECT version()')
        print(f"Connected to PostgreSQL: {version}")
        await conn.close()
    except Exception as e:
        print(f"Connection failed: {e}")

asyncio.run(test())
