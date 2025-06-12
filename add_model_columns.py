"""
Add missing columns to models table
"""
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

async def migrate():
    engine = create_async_engine(
        "postgresql+asyncpg://postgres:Th1s1s4Work@localhost:5433/webplus",
        echo=True
    )
    
    async with engine.begin() as conn:
        # Check if columns exist
        result = await conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'models' 
            AND column_name IN ('status', 'is_local', 'metadata')
        """))
        existing_columns = [row[0] for row in result]
        
        # Add missing columns
        if 'status' not in existing_columns:
            await conn.execute(text("""
                ALTER TABLE models 
                ADD COLUMN status VARCHAR DEFAULT 'inactive'
            """))
            print("Added 'status' column")
            
        if 'is_local' not in existing_columns:
            await conn.execute(text("""
                ALTER TABLE models 
                ADD COLUMN is_local BOOLEAN DEFAULT TRUE
            """))
            print("Added 'is_local' column")
            
        if 'metadata' not in existing_columns:
            await conn.execute(text("""
                ALTER TABLE models 
                ADD COLUMN metadata JSONB
            """))
            print("Added 'metadata' column")
            
        print("Migration completed!")
        
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(migrate())
