"""User caching service to avoid redundant DB lookups."""
from uuid import UUID
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncConnection

from app.core import get_settings
from app.db.users import get_or_create_user as db_get_or_create_user

# Global Redis pool
_redis_pool = None

def get_redis_client():
    global _redis_pool
    if _redis_pool is None:
        settings = get_settings()
        _redis_pool = redis.ConnectionPool.from_url(settings.REDIS_URL, decode_responses=True)
    return redis.Redis(connection_pool=_redis_pool)

async def get_cached_user_uuid(conn: AsyncConnection, firebase_uid: str) -> UUID:
    """
    Get user UUID from Redis cache or DB.
    
    Avoids overhead of INSERT ... ON CONFLICT on every request.
    """
    client = get_redis_client()
    key = f"user:firebase_uid:{firebase_uid}"
    
    # Try Redis
    try:
        cached = await client.get(key)
        if cached:
            return UUID(cached)
    except Exception:
        # If Redis fails, fall back to DB silently
        pass
        
    # DB fallback
    user_uuid, _ = await db_get_or_create_user(conn, firebase_uid)
    
    # Cache for 24 hours
    try:
        await client.set(key, str(user_uuid), ex=86400)
    except Exception:
        pass
    
    return user_uuid
