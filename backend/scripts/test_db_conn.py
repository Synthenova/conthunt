
import psycopg
import sys
import os

# Connection details from .env.local
DB_USER = os.getenv("DB_USER", "conthunt_service")
DB_PASS = os.getenv("DB_PASS", "conthunt_local")
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
# Default to PgBouncer (Docker compose); Cloud SQL proxy used 5433 historically.
DB_PORT = os.getenv("DB_PORT", "6432")
DB_NAME = os.getenv("DB_NAME", "postgres")

try:
    print(f"Connecting to {DB_HOST}:{DB_PORT} as {DB_USER}...")
    conn = psycopg.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASS,
        dbname=DB_NAME
    )
    print("Connection successful!")
    
    # Check password_encryption
    cur = conn.cursor()
    cur.execute("SHOW password_encryption;")
    row = cur.fetchone()
    print(f"Server password_encryption: {row[0]}")
    
    conn.close()
except Exception as e:
    print(f"Connection failed: {e}")
    sys.exit(1)
