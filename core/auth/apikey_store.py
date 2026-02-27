"""Redis-backed API key store: create, lookup, revoke."""
import hashlib
import json
import secrets
from typing import Optional

import redis.asyncio as aioredis

from core.config.settings import get_settings


def _hash_key(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def _redis_key(hashed: str) -> str:
    return f"apikey:{hashed}"


class APIKeyStore:
    def __init__(self, redis: aioredis.Redis):
        self._r = redis

    async def create(
        self,
        client_id: str,
        roles: list[str],
        rate_limit: int,
        description: str = "",
    ) -> str:
        """Generate raw key, store hash in Redis. Returns raw key (shown once)."""
        raw_key = secrets.token_hex(32)
        hashed  = _hash_key(raw_key)
        await self._r.hset(
            _redis_key(hashed),
            mapping={
                "client_id":   client_id,
                "roles":       json.dumps(roles),
                "rate_limit":  str(rate_limit),
                "description": description,
                "active":      "1",
            },
        )
        return raw_key

    async def lookup(self, raw_key: str) -> Optional[dict]:
        """Returns client metadata or None if not found / inactive."""
        hashed = _hash_key(raw_key)
        data   = await self._r.hgetall(_redis_key(hashed))
        if not data or data.get(b"active") != b"1":
            return None
        return {
            "client_id":  data[b"client_id"].decode(),
            "roles":      json.loads(data[b"roles"]),
            "rate_limit": int(data[b"rate_limit"]),
        }

    async def revoke(self, raw_key: str) -> bool:
        hashed = _hash_key(raw_key)
        result = await self._r.hset(_redis_key(hashed), "active", "0")
        return result is not None
