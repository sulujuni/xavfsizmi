"""
Phase 2 Cache Manager — Redis with in-memory fallback.

Provides a unified caching interface for URL scan results and other
frequently accessed data. Falls back to an LRU in-memory cache if
Redis is unavailable (e.g., local development).
"""

import os
import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional
from collections import OrderedDict

logger = logging.getLogger("safelink.cache")

# ─── CONFIG ───────────────────────────────────────────────────────────────────

REDIS_URL = os.getenv("REDIS_URL", "")  # e.g., redis://localhost:6379/0
CACHE_TTL_HOURS = int(os.getenv("CACHE_TTL_HOURS", "24"))
CACHE_PREFIX = "safelink:"
MAX_MEMORY_CACHE_SIZE = 2000  # Fallback in-memory LRU size


# ─── IN-MEMORY LRU CACHE (Fallback) ──────────────────────────────────────────

class LRUCache:
    """Simple thread-safe LRU cache for fallback when Redis is unavailable."""

    def __init__(self, max_size: int = MAX_MEMORY_CACHE_SIZE):
        self._cache: OrderedDict = OrderedDict()
        self._max_size = max_size
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[str]:
        async with self._lock:
            if key not in self._cache:
                return None
            value, expires_at = self._cache[key]
            if datetime.now() > expires_at:
                del self._cache[key]
                return None
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            return value

    async def set(self, key: str, value: str, ttl_seconds: int = 86400):
        async with self._lock:
            expires_at = datetime.now() + timedelta(seconds=ttl_seconds)
            self._cache[key] = (value, expires_at)
            self._cache.move_to_end(key)
            # Evict oldest entries if over capacity
            while len(self._cache) > self._max_size:
                self._cache.popitem(last=False)

    async def delete(self, key: str):
        async with self._lock:
            self._cache.pop(key, None)

    async def clear(self):
        async with self._lock:
            self._cache.clear()

    async def size(self) -> int:
        async with self._lock:
            return len(self._cache)


# ─── CACHE MANAGER ────────────────────────────────────────────────────────────

class CacheManager:
    """
    Unified cache interface with Redis primary and in-memory fallback.
    
    Usage:
        cache = CacheManager()
        await cache.connect()
        
        # Store URL result
        await cache.set_url_result("https://example.com", {"safe": True, ...})
        
        # Retrieve
        result = await cache.get_url_result("https://example.com")
    """

    def __init__(self):
        self._redis = None
        self._memory_cache = LRUCache()
        self._redis_available = False
        self._stats = {"hits": 0, "misses": 0, "errors": 0}

    async def connect(self):
        """Initialize Redis connection. Falls back to memory cache on failure."""
        if not REDIS_URL:
            logger.info("REDIS_URL not set — using in-memory LRU cache (max %d entries)", MAX_MEMORY_CACHE_SIZE)
            return

        try:
            import redis.asyncio as aioredis
            self._redis = aioredis.from_url(
                REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
            )
            # Test connection
            await self._redis.ping()
            self._redis_available = True
            logger.info("Redis connected successfully at %s", REDIS_URL.split("@")[-1] if "@" in REDIS_URL else REDIS_URL)
        except ImportError:
            logger.warning("redis package not installed — using in-memory cache fallback")
            self._redis = None
        except Exception as e:
            logger.warning("Redis connection failed (%s) — using in-memory cache fallback", str(e))
            self._redis = None
            self._redis_available = False

    async def disconnect(self):
        """Close Redis connection."""
        if self._redis and self._redis_available:
            try:
                await self._redis.close()
            except Exception:
                pass

    # ─── URL RESULT CACHING ───────────────────────────────────────────────────

    async def get_url_result(self, url: str) -> Optional[dict]:
        """Get cached URL scan result. Returns None if not cached or expired."""
        key = f"{CACHE_PREFIX}url:{url}"
        raw = await self._get(key)
        if raw:
            self._stats["hits"] += 1
            try:
                return json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                return None
        self._stats["misses"] += 1
        return None

    async def set_url_result(self, url: str, result: dict, ttl_hours: int = None):
        """Cache a URL scan result."""
        if ttl_hours is None:
            ttl_hours = CACHE_TTL_HOURS
        key = f"{CACHE_PREFIX}url:{url}"
        value = json.dumps(result, ensure_ascii=False)
        await self._set(key, value, ttl_seconds=ttl_hours * 3600)

    async def delete_url_result(self, url: str):
        """Remove a specific URL from cache."""
        key = f"{CACHE_PREFIX}url:{url}"
        await self._delete(key)

    # ─── GENERIC CACHING ─────────────────────────────────────────────────────

    async def get(self, key: str) -> Optional[str]:
        """Generic get with prefix."""
        return await self._get(f"{CACHE_PREFIX}{key}")

    async def set(self, key: str, value: str, ttl_seconds: int = 3600):
        """Generic set with prefix."""
        await self._set(f"{CACHE_PREFIX}{key}", value, ttl_seconds)

    async def delete(self, key: str):
        """Generic delete with prefix."""
        await self._delete(f"{CACHE_PREFIX}{key}")

    # ─── RATE LIMIT SUPPORT ───────────────────────────────────────────────────

    async def check_api_rate(self, api_name: str, max_per_minute: int) -> bool:
        """
        Check if an API call is within rate limits.
        Returns True if the call is ALLOWED, False if rate-limited.
        Uses a sliding window counter.
        """
        key = f"{CACHE_PREFIX}rate:{api_name}:{int(datetime.now().timestamp()) // 60}"

        if self._redis_available and self._redis:
            try:
                current = await self._redis.incr(key)
                if current == 1:
                    await self._redis.expire(key, 120)  # 2 min TTL for cleanup
                return current <= max_per_minute
            except Exception:
                return True  # Allow on error
        else:
            # In-memory fallback — simple counter
            raw = await self._memory_cache.get(key)
            current = int(raw) + 1 if raw else 1
            await self._memory_cache.set(key, str(current), ttl_seconds=120)
            return current <= max_per_minute

    # ─── STATS ────────────────────────────────────────────────────────────────

    def get_stats(self) -> dict:
        """Return cache hit/miss statistics."""
        total = self._stats["hits"] + self._stats["misses"]
        hit_rate = (self._stats["hits"] / total * 100) if total > 0 else 0
        return {
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "errors": self._stats["errors"],
            "hit_rate_percent": round(hit_rate, 1),
            "backend": "redis" if self._redis_available else "memory",
        }

    async def get_size(self) -> int:
        """Get approximate number of cached entries."""
        if self._redis_available and self._redis:
            try:
                # Count keys with our prefix
                count = 0
                async for _ in self._redis.scan_iter(match=f"{CACHE_PREFIX}url:*", count=100):
                    count += 1
                return count
            except Exception:
                pass
        return await self._memory_cache.size()

    async def clear_all(self):
        """Clear all cached data."""
        if self._redis_available and self._redis:
            try:
                async for key in self._redis.scan_iter(match=f"{CACHE_PREFIX}*", count=100):
                    await self._redis.delete(key)
                logger.info("Redis cache cleared")
            except Exception as e:
                logger.error("Failed to clear Redis cache: %s", e)
        await self._memory_cache.clear()
        logger.info("Memory cache cleared")

    # ─── INTERNAL METHODS ─────────────────────────────────────────────────────

    async def _get(self, key: str) -> Optional[str]:
        """Internal get — tries Redis first, falls back to memory."""
        if self._redis_available and self._redis:
            try:
                value = await self._redis.get(key)
                if value is not None:
                    return value
            except Exception as e:
                self._stats["errors"] += 1
                logger.debug("Redis GET error for %s: %s", key, e)
        # Fallback to memory
        return await self._memory_cache.get(key)

    async def _set(self, key: str, value: str, ttl_seconds: int):
        """Internal set — writes to Redis and memory cache."""
        # Always write to memory cache (backup)
        await self._memory_cache.set(key, value, ttl_seconds)

        if self._redis_available and self._redis:
            try:
                await self._redis.setex(key, ttl_seconds, value)
            except Exception as e:
                self._stats["errors"] += 1
                logger.debug("Redis SET error for %s: %s", key, e)

    async def _delete(self, key: str):
        """Internal delete from both stores."""
        await self._memory_cache.delete(key)
        if self._redis_available and self._redis:
            try:
                await self._redis.delete(key)
            except Exception as e:
                logger.debug("Redis DELETE error for %s: %s", key, e)


# ─── GLOBAL INSTANCE ──────────────────────────────────────────────────────────

cache = CacheManager()
