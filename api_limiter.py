"""
Phase 2 API Rate Limiter & Key Rotation.

Manages rate limits for external APIs (VirusTotal, Google Safe Browsing,
AlienVault, URLScan) with support for multiple API keys per service
and automatic rotation when limits are hit.

Features:
- Per-API sliding window rate limiting
- Multiple API key rotation per service
- Automatic cooldown when a key hits its limit
- Request queuing with semaphores
- Stats tracking for monitoring
"""

import os
import asyncio
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger("safelink.api_limiter")


# ─── API RATE LIMIT CONFIGURATION ────────────────────────────────────────────

@dataclass
class APIConfig:
    """Configuration for a single API service."""
    name: str
    max_per_minute: int
    max_per_day: int
    cooldown_seconds: int = 60
    keys: list = field(default_factory=list)


# Default rate limits per API (free tier)
API_CONFIGS = {
    "virustotal": APIConfig(
        name="virustotal",
        max_per_minute=4,
        max_per_day=500,
        cooldown_seconds=60,
    ),
    "google_safe_browsing": APIConfig(
        name="google_safe_browsing",
        max_per_minute=100,
        max_per_day=10000,
        cooldown_seconds=10,
    ),
    "alienvault": APIConfig(
        name="alienvault",
        max_per_minute=20,
        max_per_day=1000,
        cooldown_seconds=30,
    ),
    "urlscan": APIConfig(
        name="urlscan",
        max_per_minute=10,
        max_per_day=1000,
        cooldown_seconds=30,
    ),
}


# ─── KEY MANAGER ──────────────────────────────────────────────────────────────

@dataclass
class APIKeyState:
    """Tracks usage state for a single API key."""
    key: str
    requests_this_minute: int = 0
    requests_today: int = 0
    minute_reset: datetime = field(default_factory=datetime.now)
    day_reset: datetime = field(default_factory=lambda: datetime.now().replace(hour=0, minute=0, second=0) + timedelta(days=1))
    cooldown_until: Optional[datetime] = None
    total_requests: int = 0
    total_errors: int = 0

    def is_available(self) -> bool:
        """Check if this key can accept requests right now."""
        now = datetime.now()

        # Check cooldown
        if self.cooldown_until and now < self.cooldown_until:
            return False

        # Reset minute counter
        if (now - self.minute_reset).total_seconds() >= 60:
            self.requests_this_minute = 0
            self.minute_reset = now

        # Reset day counter
        if now >= self.day_reset:
            self.requests_today = 0
            self.day_reset = now.replace(hour=0, minute=0, second=0) + timedelta(days=1)

        return True

    def record_use(self):
        """Record that this key was used for a request."""
        now = datetime.now()
        if (now - self.minute_reset).total_seconds() >= 60:
            self.requests_this_minute = 0
            self.minute_reset = now
        self.requests_this_minute += 1
        self.requests_today += 1
        self.total_requests += 1

    def record_error(self, cooldown_seconds: int = 60):
        """Record an error (rate limit hit) and set cooldown."""
        self.total_errors += 1
        self.cooldown_until = datetime.now() + timedelta(seconds=cooldown_seconds)
        logger.warning("API key %s...%s put on cooldown for %ds",
                       self.key[:8], self.key[-4:], cooldown_seconds)


class KeyRotator:
    """
    Manages multiple API keys for a service with round-robin rotation.
    
    Load keys from environment variables:
    - VIRUSTOTAL_API_KEY (primary)
    - VIRUSTOTAL_API_KEY_2, VIRUSTOTAL_API_KEY_3, etc. (additional)
    """

    def __init__(self, api_name: str, config: APIConfig):
        self.api_name = api_name
        self.config = config
        self._keys: list[APIKeyState] = []
        self._current_index = 0
        self._lock = asyncio.Lock()
        self._load_keys()

    def _load_keys(self):
        """Load API keys from environment variables."""
        env_prefix = self.api_name.upper()

        # Primary key
        primary_key = os.getenv(f"{env_prefix}_API_KEY", "")
        if primary_key and "Sizning" not in primary_key:
            self._keys.append(APIKeyState(key=primary_key))

        # Additional keys: _API_KEY_2, _API_KEY_3, etc.
        for i in range(2, 11):
            extra_key = os.getenv(f"{env_prefix}_API_KEY_{i}", "")
            if extra_key and "Sizning" not in extra_key:
                self._keys.append(APIKeyState(key=extra_key))

        if self._keys:
            logger.info("Loaded %d API key(s) for %s", len(self._keys), self.api_name)
        else:
            logger.warning("No API keys found for %s", self.api_name)

    async def get_key(self) -> Optional[str]:
        """
        Get the next available API key using round-robin rotation.
        Returns None if all keys are on cooldown or no keys available.
        """
        if not self._keys:
            return None

        async with self._lock:
            # Try each key starting from current index
            for _ in range(len(self._keys)):
                key_state = self._keys[self._current_index]
                self._current_index = (self._current_index + 1) % len(self._keys)

                if key_state.is_available():
                    # Check per-minute limit
                    if key_state.requests_this_minute >= self.config.max_per_minute:
                        continue
                    # Check per-day limit
                    if key_state.requests_today >= self.config.max_per_day:
                        continue
                    return key_state.key

            # All keys exhausted
            logger.warning("All %d keys for %s are rate-limited or on cooldown",
                           len(self._keys), self.api_name)
            return None

    async def record_success(self, key: str):
        """Record a successful API call."""
        async with self._lock:
            for key_state in self._keys:
                if key_state.key == key:
                    key_state.record_use()
                    break

    async def record_failure(self, key: str, is_rate_limit: bool = False):
        """Record a failed API call. If rate limited, apply cooldown."""
        async with self._lock:
            for key_state in self._keys:
                if key_state.key == key:
                    if is_rate_limit:
                        key_state.record_error(self.config.cooldown_seconds)
                    else:
                        key_state.total_errors += 1
                    break

    def get_stats(self) -> dict:
        """Get usage stats for all keys in this rotator."""
        return {
            "api_name": self.api_name,
            "total_keys": len(self._keys),
            "keys": [
                {
                    "key_prefix": f"{ks.key[:8]}...",
                    "requests_this_minute": ks.requests_this_minute,
                    "requests_today": ks.requests_today,
                    "total_requests": ks.total_requests,
                    "total_errors": ks.total_errors,
                    "on_cooldown": ks.cooldown_until is not None and datetime.now() < ks.cooldown_until,
                    "available": ks.is_available(),
                }
                for ks in self._keys
            ]
        }


# ─── RATE LIMITER ─────────────────────────────────────────────────────────────

class APIRateLimiter:
    """
    Central rate limiter for all external API calls.
    
    Usage:
        limiter = APIRateLimiter()
        
        # Before making an API call
        key = await limiter.acquire("virustotal")
        if key is None:
            # All keys rate limited, use cached result or skip
            return fallback_result
        
        try:
            result = await make_api_call(key)
            await limiter.release("virustotal", key, success=True)
        except RateLimitError:
            await limiter.release("virustotal", key, success=False, is_rate_limit=True)
    """

    def __init__(self):
        self._rotators: dict[str, KeyRotator] = {}
        self._semaphores: dict[str, asyncio.Semaphore] = {}
        self._queue_stats: dict[str, int] = {}
        self._init_rotators()

    def _init_rotators(self):
        """Initialize key rotators and semaphores for each API."""
        for api_name, config in API_CONFIGS.items():
            self._rotators[api_name] = KeyRotator(api_name, config)
            # Semaphore limits concurrent requests per API
            self._semaphores[api_name] = asyncio.Semaphore(config.max_per_minute)
            self._queue_stats[api_name] = 0

    async def acquire(self, api_name: str, timeout: float = 30.0) -> Optional[str]:
        """
        Acquire an API key for making a request.
        Waits up to timeout seconds for a semaphore slot.
        Returns the API key to use, or None if unavailable.
        """
        if api_name not in self._rotators:
            logger.error("Unknown API: %s", api_name)
            return None

        self._queue_stats[api_name] = self._queue_stats.get(api_name, 0) + 1

        try:
            # Wait for semaphore with timeout
            await asyncio.wait_for(
                self._semaphores[api_name].acquire(),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            self._queue_stats[api_name] -= 1
            logger.warning("Timeout waiting for %s semaphore", api_name)
            return None

        self._queue_stats[api_name] -= 1

        # Get available key
        key = await self._rotators[api_name].get_key()
        if key is None:
            # No key available — release semaphore
            self._semaphores[api_name].release()
            return None

        return key

    async def release(self, api_name: str, key: str, success: bool = True, is_rate_limit: bool = False):
        """
        Release the semaphore and record the result.
        Call after the API request completes.
        """
        if api_name not in self._rotators:
            return

        # Release semaphore
        self._semaphores[api_name].release()

        # Record result
        if success:
            await self._rotators[api_name].record_success(key)
        else:
            await self._rotators[api_name].record_failure(key, is_rate_limit=is_rate_limit)

    async def is_available(self, api_name: str) -> bool:
        """Check if any key is available for this API (quick check without blocking)."""
        if api_name not in self._rotators:
            return False
        key = await self._rotators[api_name].get_key()
        return key is not None

    def get_stats(self) -> dict:
        """Get stats for all APIs."""
        return {
            api_name: {
                **rotator.get_stats(),
                "queue_waiting": self._queue_stats.get(api_name, 0),
            }
            for api_name, rotator in self._rotators.items()
        }

    def get_api_stats(self, api_name: str) -> Optional[dict]:
        """Get stats for a specific API."""
        if api_name not in self._rotators:
            return None
        return {
            **self._rotators[api_name].get_stats(),
            "queue_waiting": self._queue_stats.get(api_name, 0),
        }


# ─── GLOBAL INSTANCE ──────────────────────────────────────────────────────────

rate_limiter = APIRateLimiter()
