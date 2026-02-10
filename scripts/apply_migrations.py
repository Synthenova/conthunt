import asyncio
import asyncpg
import os
import sys
from pathlib import Path

# NOTE: Deprecated.
# Use Alembic instead:
#   cd backend
#   alembic upgrade head
#
# Configuration
SQL_DIR = Path("backend/.sqls")
# Default to local proxy if not set

async def apply_migrations(db_url):
    print(f"Connecting to {db_url}...")
    try:
        conn = await asyncpg.connect(db_url)
    except Exception as e:
        print(f"Failed to connect: {e}")
        print("Ensure cloud-sql-proxy is running and credentials are correct.")
        return

    print("Connected!")
    
    # Get all SQL files sorted
    files = sorted([f for f in os.listdir(SQL_DIR) if f.endswith('.sql')])
    
    if not files:
        print("No SQL files found in backend/.sqls")
        return

    print(f"Found {len(files)} migration files.")
    
    # Allow skipping
    start_from = input("Start from file (prefix, e.g. 003) [Enter for all]: ").strip()
    if start_from:
        files = [f for f in files if f >= start_from]
        print(f"Starting from: {files[0] if files else 'None'}")

    # Ensure schema exists
    try:
        print("Ensuring schema 'conthunt' exists...", end=" ", flush=True)
        await conn.execute("CREATE SCHEMA IF NOT EXISTS conthunt;")
        await conn.execute("SET search_path TO conthunt;")
        print("OK")
    except Exception as e:
        print(f"FAILED to create schema: {e}")
        return

    for filename in files:
        filepath = SQL_DIR / filename
        print(f"Applying {filename}...", end=" ", flush=True)
        
        with open(filepath, 'r') as f:
            sql_content = f.read()
        
        try:
            # Run each file in its own transaction.
            async with conn.transaction():
                await conn.execute(sql_content)
            print("OK")
        except Exception as e:
            print(f"FAILED!")
            print(f"Error in {filename}: {e}")
            # Stop on first error
            sys.exit(1)

    print("\nAll migrations applied successfully!")
    await conn.close()

import getpass

if __name__ == "__main__":
    if len(sys.argv) > 1:
        db_url = sys.argv[1]
    else:
        print("No DB URL provided.")
        username = input("Enter Cloud SQL Username (default: nirmal): ").strip() or "conthunt_app"
        password = getpass.getpass("Enter Cloud SQL Password: ")
        dbname = input("Enter Database Name (default: conthunt): ").strip() or "postgres"
        
        # Construct URL with defaults for prod proxy
        db_url = f"postgresql://{username}:{password}@127.0.0.1:5433/{dbname}"
        
    # Warn user
    # Mask password in print
    safe_url = db_url.split('@')[-1]
    print(f"Target Database: postgresql://...@{safe_url}")
    
    confirm = input("Continue? (y/N): ")
    if confirm.lower() != 'y':
        print("Aborted.")
        sys.exit(0)

    asyncio.run(apply_migrations(db_url))
