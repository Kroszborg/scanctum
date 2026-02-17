import asyncio
import sys

sys.path.insert(0, "C:/programming/scanctum/backend")

from app.db.base import Base
from app.db.engine import async_engine
from app.models import *  # noqa - import all models


async def create_tables():
    """Create all database tables."""
    print("Creating all tables...")
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created successfully!")
    
    # List tables
    async with async_engine.connect() as conn:
        from sqlalchemy import text
        result = await conn.execute(
            text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)
        )
        tables = result.fetchall()
        
        print("\nTables in database:")
        for table in tables:
            print(f"  - {table[0]}")


if __name__ == "__main__":
    asyncio.run(create_tables())
