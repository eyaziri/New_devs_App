import json
import redis.asyncio as redis
from typing import Dict, Any
import os

# Initialize Redis client (typically configured centrally).
redis_client = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))

#----------------------------------------------
# thread month/year through and scope the cache key by period
#----------------------------------------------

async def get_revenue_summary(property_id: str, tenant_id: str, month: int, year: int) -> Dict[str, Any]:
    """
    Fetches a tenant- and period-scoped revenue summary, utilizing caching to
    avoid cross-tenant leakage and stale cross-month results.
    """
    #---------------------------------
    # Cache key scoped by tenant, property, and month/year
    #---------------------------------
    cache_key = f"revenue:{tenant_id}:{property_id}:{year:04d}-{month:02d}"

    cached = await redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    from app.services.reservations import calculate_total_revenue

    result = await calculate_total_revenue(property_id, tenant_id, month, year)
    await redis_client.setex(cache_key, 300, json.dumps(result))
    return result
