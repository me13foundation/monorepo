"""Shared rate limiting backed by Redis."""

from __future__ import annotations

import importlib
import logging
import os
from typing import TYPE_CHECKING, Protocol, TypeGuard

if TYPE_CHECKING:
    from types import ModuleType

logger = logging.getLogger(__name__)


class RedisClientProtocol(Protocol):
    async def incr(self, key: str) -> int:
        ...

    async def expire(self, key: str, seconds: int) -> int | bool:
        ...

    async def ttl(self, key: str) -> int | None:
        ...

    async def close(self) -> None:
        ...


class RedisFactory(Protocol):
    @classmethod
    def from_url(cls, redis_url: str) -> RedisClientProtocol:
        ...


def _load_redis_factory() -> type[RedisFactory]:
    """Load the Redis factory class without requiring type stubs."""
    try:
        module: ModuleType = importlib.import_module("redis.asyncio")
    except ImportError as exc:  # pragma: no cover - optional dependency
        msg = "redis package not installed"
        raise RuntimeError(msg) from exc

    factory_obj: object = getattr(module, "Redis", None)
    if not _is_redis_factory(factory_obj):
        msg = "redis.asyncio.Redis not available"
        raise RuntimeError(msg)

    return factory_obj


class DistributedRateLimiter:
    """Simple fixed-window rate limiter backed by Redis."""

    def __init__(
        self,
        redis_url: str,
        window_seconds: int = 60,
    ) -> None:
        redis_factory = _load_redis_factory()
        self.redis = redis_factory.from_url(redis_url)
        self.window_seconds = window_seconds

    async def allow(self, key: str, capacity: int) -> tuple[bool, int]:
        """
        Increment usage for the key and return whether the request is allowed.

        Returns:
            Tuple[allowed, retry_after_seconds]
        """
        value = await self.redis.incr(key)
        if value == 1:
            await self.redis.expire(key, self.window_seconds)
        ttl = await self.redis.ttl(key)
        if ttl is None or ttl < 0:
            ttl = self.window_seconds
        return value <= capacity, int(ttl)

    async def close(self) -> None:
        """Close the Redis connection."""
        await self.redis.close()


def build_distributed_limiter() -> DistributedRateLimiter | None:
    """Create a distributed limiter if configuration is present."""
    enabled = os.getenv("MED13_ENABLE_DISTRIBUTED_RATE_LIMIT", "1")
    if enabled != "1":
        logger.info(
            "Distributed rate limiting disabled (MED13_ENABLE_DISTRIBUTED_RATE_LIMIT=%s)",
            enabled,
        )
        return None
    redis_url = os.getenv("MED13_RATE_LIMIT_REDIS_URL")
    if not redis_url:
        return None
    return DistributedRateLimiter(redis_url=redis_url)


def _is_redis_factory(obj: object) -> TypeGuard[type[RedisFactory]]:
    if obj is None or not hasattr(obj, "from_url"):
        return False
    from_url = obj.from_url
    return callable(from_url)
