"""User caching service to avoid redundant DB lookups."""
from uuid import UUID
import redis.asyncio as redis
from cachetools import TTLCache
from sqlalchemy.ext.asyncio import AsyncConnection

from app.core import get_settings
from app.db.users import get_or_create_user as db_get_or_create_user
from app.db.decorators import log_query_timing

# Global Redis pool
_redis_pool = None
# Local L1 Cache (5 minutes TTL, max 1000 users)
_local_cache = TTLCache(maxsize=1000, ttl=300)

def get_redis_client():
    global _redis_pool
    if _redis_pool is None:
        settings = get_settings()
        _redis_pool = redis.ConnectionPool.from_url(settings.REDIS_URL, decode_responses=True)
    return redis.Redis(connection_pool=_redis_pool)

# @log_query_timing
async def get_cached_user_uuid(conn: AsyncConnection, firebase_uid: str) -> UUID:
    """
    Get user UUID from:
    1. Local Memory (L1)
    2. Redis (L2)
    3. DB (L3)
    """
    # 1. Try L1 Cache
    if firebase_uid in _local_cache:
        return _local_cache[firebase_uid]

    client = get_redis_client()
    key = f"user:firebase_uid:{firebase_uid}"
    
    # 2. Try Redis (L2)
    try:
        cached = await client.get(key)
        if cached:
            user_uuid = UUID(cached)
            _local_cache[firebase_uid] = user_uuid
            return user_uuid
    except Exception:
        # Fallback silently
        pass
        
    # 3. DB Fallback (L3)
    user_uuid, _ = await db_get_or_create_user(conn, firebase_uid)
    
    # Update Caches
    _local_cache[firebase_uid] = user_uuid
    try:
        await client.set(key, str(user_uuid), ex=86400)
    except Exception:
        pass
    
    return user_uuid
