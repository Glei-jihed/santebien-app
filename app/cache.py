import json
import os
from typing import Any

from redis.asyncio import Redis


class Cache:
    """Redis cache with a local fallback for development and tests."""

    def __init__(self) -> None:
        self.redis = Redis.from_url(
            os.getenv("REDIS_URL", "redis://localhost:6379/0"),
            decode_responses=True,
            socket_connect_timeout=0.2,
        )
        self.local: dict[str, str] = {}
        self.hits = 0
        self.misses = 0
        self.backend = "redis"

    async def connect(self) -> None:
        try:
            await self.redis.ping()
        except Exception:
            self.backend = "memory"

    async def get(self, key: str) -> Any | None:
        try:
            raw = await self.redis.get(key) if self.backend == "redis" else self.local.get(key)
        except Exception:
            self.backend = "memory"
            raw = self.local.get(key)

        if raw is None:
            self.misses += 1
            return None

        self.hits += 1
        return json.loads(raw)

    async def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        raw = json.dumps(value, default=str)
        try:
            if self.backend == "redis":
                await self.redis.setex(key, ttl, raw)
            else:
                self.local[key] = raw
        except Exception:
            self.backend = "memory"
            self.local[key] = raw

    async def delete_pattern(self, pattern: str) -> None:
        if self.backend == "redis":
            try:
                keys = [key async for key in self.redis.scan_iter(match=pattern)]
                if keys:
                    await self.redis.delete(*keys)
                return
            except Exception:
                self.backend = "memory"

        prefix = pattern.removesuffix("*")
        for key in list(self.local):
            if key.startswith(prefix):
                del self.local[key]

    def stats(self) -> dict[str, Any]:
        total = self.hits + self.misses
        return {
            "backend": self.backend,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate_percent": round(self.hits / total * 100, 2) if total else 0,
        }
