"""API key lifecycle management.

Raw keys are shown to the user once and never stored.
Only the SHA-256 hash is stored — in Redis (hot cache) and SQLite (durable).
"""

import hashlib
import json
import secrets
from datetime import datetime

from redis.asyncio import Redis

from core.auth.models import APIKey

REDIS_PREFIX = "apikey:"


def hash_key(raw_key: str) -> str:
    """SHA-256 hash of raw key. Used as Redis field and SQLite lookup."""
    return hashlib.sha256(raw_key.encode()).hexdigest()


def generate_raw_key() -> str:
    """Generate a cryptographically secure 64-char hex API key."""
    return secrets.token_hex(32)


async def cache_key_in_redis(redis: Redis, api_key: APIKey) -> None:
    """Store API key metadata in Redis hash for fast auth lookups."""
    await redis.hset(
        f"{REDIS_PREFIX}{api_key.key_hash}",
        mapping={
            "client_id":  api_key.client_id,
            "roles":      api_key.roles,          # JSON string
            "rate_limit": str(api_key.rate_limit),
            "active":     "1" if api_key.is_active else "0",
        },
    )


async def lookup_key_in_redis(redis: Redis, raw_key: str) -> dict | None:
    """Lookup API key by raw value. Returns metadata dict or None."""
    key_hash = hash_key(raw_key)
    data = await redis.hgetall(f"{REDIS_PREFIX}{key_hash}")
    if not data or data.get(b"active", b"0") == b"0":
        return None
    return {
        "client_id":  data[b"client_id"].decode(),
        "roles":      json.loads(data[b"roles"].decode()),
        "rate_limit": int(data[b"rate_limit"]),
    }


async def revoke_key_in_redis(redis: Redis, key_hash: str) -> None:
    """Mark key as inactive in Redis. SQLite update done separately."""
    await redis.hset(f"{REDIS_PREFIX}{key_hash}", "active", "0")
