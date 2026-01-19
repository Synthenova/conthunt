
import psycopg
import sys

# Connection details from .env.local
DB_USER = "conthunt_service"
DB_PASS = ""
DB_HOST = "127.0.0.1"
DB_PORT = "5433"
DB_NAME = "postgres"

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
