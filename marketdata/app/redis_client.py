"""Async Redis client for streaming queue; lifecycle via get_redis / close_redis."""

import os
from typing import Optional

_redis: Optional["redis.asyncio.Redis"] = None


async def get_redis() -> "redis.asyncio.Redis":
    """Return shared async Redis connection; create if needed."""
    global _redis
    if _redis is None:
        import redis.asyncio as redis
        url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        _redis = redis.from_url(url, decode_responses=True)
    return _redis


async def close_redis() -> None:
    """Close Redis connection (call on app shutdown)."""
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None
