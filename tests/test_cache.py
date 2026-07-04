"""Tests for the in-memory cache layer (the Redis-less fallback path)."""
import time

from cache import _MemoryCache, Cache


def test_set_get_delete():
    c = _MemoryCache()
    c.set("a", "1")
    assert c.get("a") == "1"
    c.delete("a")
    assert c.get("a") is None


def test_ttl_expiry():
    c = _MemoryCache()
    c.set("k", "v", ttl=1)
    assert c.get("k") == "v"
    # Simulate expiry without sleeping a full second by rewriting the expiry.
    value, _ = c._data["k"]
    c._data["k"] = (value, time.time() - 1)
    assert c.get("k") is None


def test_size_cap_eviction():
    c = _MemoryCache(max_size=3)
    for i in range(5):
        c.set(f"k{i}", str(i))
    assert c.size() <= 3


def test_cache_backend_defaults_to_memory():
    c = Cache()
    # No REDIS_URL in tests -> memory backend, no exceptions.
    c.connect()
    assert c.backend == "memory"
    c.set("x", "y")
    assert c.get("x") == "y"
    stats = c.stats()
    assert stats["backend"] == "memory"
    assert stats["hits"] >= 1
