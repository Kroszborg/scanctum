import asyncio
import sys

sys.path.insert(0, "C:/programming/scanctum/backend")

from app.db.engine import async_engine
from sqlalchemy import text


async def check_tables():
    """Check what tables exist in the database."""
    async with async_engine.connect() as conn:
        result = await conn.execute(
            text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)
        )
        tables = result.fetchall()
        
        if tables:
            print("Existing tables in database:")
            for table in tables:
                print(f"  - {table[0]}")
        else:
            print("No tables found in database")


if __name__ == "__main__":
    asyncio.run(check_tables())
