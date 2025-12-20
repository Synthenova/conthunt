
import asyncio
import sys
import os
from uuid import UUID

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))

from app.db.session import get_db_connection
from app.db.queries.content import get_content_item_by_id
from sqlalchemy import text

async def main():
    print("Verifying get_content_item_by_id CDN signing...")
    
    async with get_db_connection() as conn:
        # 1. Find a content item with a GCS URI
        result = await conn.execute(text("""
            SELECT content_item_id, gcs_uri 
            FROM media_assets 
            WHERE gcs_uri IS NOT NULL 
            LIMIT 1
        """))
        row = result.fetchone()
        
        if not row:
            print("No media assets with GCS URI found. Cannot verify CDN signing logic fully.")
            # Verify fallback logic at least
            # Find any content item
            result = await conn.execute(text("SELECT id FROM content_items LIMIT 1"))
            row = result.fetchone()
            if not row:
                print("No content items found at all.")
                return

            print("Testing fallback logic (no GCS URI)...")
            item = await get_content_item_by_id(conn, row[0])
            print(f"Video URL: {item.get('video_url')}")
            # Should be source_url or None. 
            # We can't easily assert correctness without knowing the source_url, 
            # but we know it SHOULDN'T be a signed URL.
            if item.get('video_url') and "Signature=" in item.get('video_url'):
                print("FAIL: Got signed URL when no GCS URI expected (or fallback failed)")
            else:
                print("SUCCESS: Fallback logic seems okay (not signed).")
            return

        content_item_id = row[0]
        gcs_uri = row[1]
        print(f"Found content item {content_item_id} with GCS URI {gcs_uri}")
        
        # 2. Call the function
        item = await get_content_item_by_id(conn, content_item_id)
        
        if not item:
            print("FAIL: Content item not found via get_content_item_by_id")
            return

        video_url = item.get("video_url")
        print(f"Returned video_url: {video_url}")
        
        # 3. Assertions
        if not video_url:
            print("FAIL: video_url is None")
            return
            
        if "Signature=" not in video_url:
            print("FAIL: video_url does not contain Signature")
            return
            
        if "Expires=" not in video_url:
            print("FAIL: video_url does not contain Expires")
            return
            
        if "KeyName=" not in video_url:
            print("FAIL: video_url does not contain KeyName")
            return

        print("SUCCESS: video_url matches signed URL format.")

if __name__ == "__main__":
    asyncio.run(main())
