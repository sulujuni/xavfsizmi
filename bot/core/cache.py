"""
Synchronous cache layer for SafeLink Bot (Phase 2).

Provides a Redis-backed cache with an automatic in-memory fallback when
REDIS_URL is unset or Redis is unreachable. All methods are synchronous so
they can be called directly from the existing (synchronous) database layer
without touching any handler code.

Used as a write-through cache in front of the SQLite document store, and as
a TTL cache for URL scan results.
"""

import os
import time
import logging
import threading

logger = logging.getLogger("safelink.cache")

REDIS_URL = os.getenv("REDIS_URL", "")
KEY_PREFIX = os.getenv("CACHE_PREFIX", "safelink:")
# Default TTL for URL scan results (hours -> seconds)
URL_CACHE_TTL = int(os.getenv("CACHE_TTL_HOURS", "24")) * 3600
MAX_MEMORY_ENTRIES = int(os.getenv("CACHE_MAX_MEMORY", "10000"))



class _MemoryCache:
    """Thread-safe in-memory cache with TTL and simple size-capped eviction."""

    def __init__(self, max_size: int = MAX_MEMORY_ENTRIES):
        self._data = {}  # key -> (value, expires_at_epoch or 0)
        self._lock = threading.RLock()
        self._max = max_size

    def get(self, key: str):
        with self._lock:
            item = self._data.get(key)
            if item is None:
                return None
            value, expires = item
            if expires and time.time() > expires:
                self._data.pop(key, None)
                return None
            return value

    def set(self, key: str, value: str, ttl: int = 0):
        with self._lock:
            expires = time.time() + ttl if ttl else 0
            # Evict an arbitrary (oldest-inserted) entry if at capacity
            if key not in self._data and len(self._data) >= self._max:
                self._data.pop(next(iter(self._data)), None)
            self._data[key] = (value, expires)

    def delete(self, key: str):
        with self._lock:
            self._data.pop(key, None)

    def clear(self):
        with self._lock:
            self._data.clear()

    def size(self) -> int:
        with self._lock:
            return len(self._data)



class Cache:
    """
    Unified cache. Tries Redis first (if configured/reachable), always keeps a
    local in-memory copy as a fast L1 / fallback. Values are strings.
    """

    def __init__(self):
        self._redis = None
        self._redis_ok = False
        self._mem = _MemoryCache()
        self._stats = {"hits": 0, "misses": 0, "errors": 0}

    def connect(self):
        """Initialize Redis. Safe to call once at startup. Never raises."""
        if not REDIS_URL:
            logger.info("REDIS_URL not set - using in-memory cache (max %d entries)", MAX_MEMORY_ENTRIES)
            return
        try:
            import redis  # redis-py (synchronous client)
            self._redis = redis.from_url(
                REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            self._redis.ping()
            self._redis_ok = True
            logger.info("Redis cache connected")
        except ImportError:
            logger.warning("redis package not installed - using in-memory cache fallback")
            self._redis = None
        except Exception as e:
            logger.warning("Redis connection failed (%s) - using in-memory cache fallback", e)
            self._redis = None
            self._redis_ok = False

    @property
    def backend(self) -> str:
        return "redis" if self._redis_ok else "memory"

    def _k(self, key: str) -> str:
        return f"{KEY_PREFIX}{key}"



    def get(self, key: str):
        """Return cached string value or None. Checks memory first, then Redis."""
        # L1 memory
        v = self._mem.get(key)
        if v is not None:
            self._stats["hits"] += 1
            return v
        # L2 redis
        if self._redis_ok:
            try:
                rv = self._redis.get(self._k(key))
                if rv is not None:
                    self._mem.set(key, rv)  # populate L1
                    self._stats["hits"] += 1
                    return rv
            except Exception:
                self._stats["errors"] += 1
        self._stats["misses"] += 1
        return None

    def set(self, key: str, value: str, ttl: int = 0):
        """Store a string value with optional TTL (seconds; 0 = no expiry)."""
        self._mem.set(key, value, ttl)
        if self._redis_ok:
            try:
                if ttl:
                    self._redis.setex(self._k(key), ttl, value)
                else:
                    self._redis.set(self._k(key), value)
            except Exception:
                self._stats["errors"] += 1

    def delete(self, key: str):
        self._mem.delete(key)
        if self._redis_ok:
            try:
                self._redis.delete(self._k(key))
            except Exception:
                self._stats["errors"] += 1

    def clear_prefix(self, prefix: str):
        """Delete all keys under a logical prefix (best effort)."""
        self._mem.clear()
        if self._redis_ok:
            try:
                for k in self._redis.scan_iter(match=f"{KEY_PREFIX}{prefix}*", count=200):
                    self._redis.delete(k)
            except Exception:
                self._stats["errors"] += 1

    def stats(self) -> dict:
        total = self._stats["hits"] + self._stats["misses"]
        hit_rate = (self._stats["hits"] / total * 100) if total else 0.0
        return {
            "backend": self.backend,
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "errors": self._stats["errors"],
            "hit_rate_percent": round(hit_rate, 1),
            "memory_entries": self._mem.size(),
        }


# Global shared instance used by the database layer.
cache = Cache()
