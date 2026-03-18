"""LRU cache for frequently accessed data."""

import asyncio
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

import redis.asyncio as redis

from app.config import settings

T = TypeVar("T")

# Global cache instance
_cache: redis.Redis | None = None


async def get_redis() -> redis.Redis:
    """Get or create Redis connection with pooling."""
    global _cache
    if _cache is None:
        _cache = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=5,
            socket_keepalive=True,
            socket_keepalive_options={
                1: 60,  # TCP_KEEPIDLE
                2: 60,  # TCP_KEEPINTVL
                3: 3,   # TCP_KEEPCNT
            },
        )
    return _cache


def cached(
    key_prefix: str,
    ttl: int = 300,
    key_fn: Callable[..., str] | None = None,
):
    """
    Decorator to cache async function results in Redis.

    Args:
        key_prefix: Prefix for cache keys
        ttl: Time to live in seconds (default: 5 minutes)
        key_fn: Optional function to generate cache key from args
    """
    def decorator(func: Callable[..., Any]):
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Generate cache key
            if key_fn:
                cache_key = f"{key_prefix}:{key_fn(*args, **kwargs)}"
            else:
                # Default: use first arg (usually user_id or scan_id)
                key_arg = args[0] if args else "default"
                cache_key = f"{key_prefix}:{key_arg}"

            # Try cache
            r = await get_redis()
            try:
                cached_data = await r.get(cache_key)
                if cached_data:
                    import json
                    return json.loads(cached_data)
            except Exception:
                pass  # Cache miss or error, continue to function

            # Execute function
            result = await func(*args, **kwargs)

            # Store in cache
            try:
                import json
                await r.setex(cache_key, ttl, json.dumps(result, default=str))
            except Exception:
                pass  # Cache write error, still return result

            return result

        return wrapper
    return decorator


async def invalidate_cache(key_prefix: str, key: str) -> None:
    """Invalidate a specific cache key."""
    r = await get_redis()
    try:
        await r.delete(f"{key_prefix}:{key}")
    except Exception:
        pass


async def invalidate_pattern(pattern: str) -> None:
    """Invalidate all cache keys matching a pattern."""
    r = await get_redis()
    try:
        keys = await r.keys(pattern)
        if keys:
            await r.delete(*keys)
    except Exception:
        pass


class LRUCache:
    """
    In-memory LRU cache for hot data.
    Used as a first-level cache before Redis.
    """

    def __init__(self, max_size: int = 1000):
        self._cache: dict[str, Any] = {}
        self._order: list[str] = []
        self._max_size = max_size
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Any | None:
        async with self._lock:
            if key in self._cache:
                # Move to end (most recently used)
                self._order.remove(key)
                self._order.append(key)
                return self._cache[key]
            return None

    async def set(self, key: str, value: Any) -> None:
        async with self._lock:
            if key in self._cache:
                self._order.remove(key)
            elif len(self._cache) >= self._max_size:
                # Evict oldest
                oldest = self._order.pop(0)
                del self._cache[oldest]

            self._cache[key] = value
            self._order.append(key)

    async def delete(self, key: str) -> None:
        async with self._lock:
            if key in self._cache:
                self._order.remove(key)
                del self._cache[key]

    async def clear(self) -> None:
        async with self._lock:
            self._cache.clear()
            self._order.clear()


# Global in-memory cache for hot data
hot_cache = LRUCache(max_size=500)
