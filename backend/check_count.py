
import asyncio
import os
from app.db import get_db_connection
from textwrap import dedent

async def check():
    search_id = "2e46ae9b-a053-4530-a3b0-d0b87029268e"
    async with get_db_connection() as conn:
        row = await conn.fetchrow("SELECT count(*) FROM search_results WHERE search_id = $1", search_id)
        print(f"Count: {row['count']}")

if __name__ == "__main__":
    asyncio.run(check())
