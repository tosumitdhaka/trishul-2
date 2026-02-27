from __future__ import annotations

import hashlib
import json
import secrets
from typing import Any

import redis.asyncio as aioredis


def _hash_key(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def generate_raw_key() -> str:
    """Generate a secure random API key (hex, 64 chars)."""
    return secrets.token_hex(32)


async def store_api_key(
    redis: aioredis.Redis,
    raw_key: str,
    client_id: str,
    roles: list[str],
    rate_limit: int = 60,
    description: str = "",
) -> str:
    """Hash + persist API key to Redis. Returns the hash (stored ID)."""
    key_hash = _hash_key(raw_key)
    mapping: dict[str, Any] = {
        "client_id":   client_id,
        "roles":       json.dumps(roles),
        "rate_limit":  rate_limit,
        "description": description,
        "active":      "1",
    }
    await redis.hset(f"apikey:{key_hash}", mapping=mapping)  # type: ignore[arg-type]
    return key_hash


async def lookup_api_key(
    redis: aioredis.Redis,
    raw_key: str,
) -> dict[str, Any] | None:
    """Returns client metadata or None if key not found / inactive."""
    key_hash = _hash_key(raw_key)
    data = await redis.hgetall(f"apikey:{key_hash}")
    if not data or data.get(b"active", b"0") == b"0":
        return None
    return {
        "client_id":  data[b"client_id"].decode(),
        "roles":      json.loads(data[b"roles"]),
        "rate_limit": int(data[b"rate_limit"]),
    }


async def revoke_api_key(redis: aioredis.Redis, raw_key: str) -> None:
    key_hash = _hash_key(raw_key)
    await redis.hset(f"apikey:{key_hash}", "active", "0")


async def add_to_blocklist(redis: aioredis.Redis, jti: str, ttl_seconds: int) -> None:
    await redis.set(f"blocklist:{jti}", "1", ex=ttl_seconds)


async def is_blocklisted(redis: aioredis.Redis, jti: str) -> bool:
    return bool(await redis.exists(f"blocklist:{jti}"))
