from __future__ import annotations

import json
from typing import Any

from redis import Redis

from app.config import get_settings

KNOWLEDGE_BASE_VERSION_KEY = "kb:version"


def get_redis_client() -> Redis:
    settings = get_settings()
    return Redis.from_url(
        settings.redis_url,
        decode_responses=True,
        socket_connect_timeout=2,
        socket_timeout=2,
    )


def ping_redis() -> bool:
    try:
        return bool(get_redis_client().ping())
    except Exception:
        return False


def get_json(key: str) -> dict[str, Any] | None:
    try:
        raw_value = get_redis_client().get(key)
    except Exception:
        return None
    if not raw_value:
        return None
    try:
        value = json.loads(raw_value)
    except json.JSONDecodeError:
        delete_key(key)
        return None
    return value if isinstance(value, dict) else None


def set_json(key: str, value: dict[str, Any], ttl_seconds: int) -> bool:
    try:
        return bool(
            get_redis_client().set(
                key,
                json.dumps(value, ensure_ascii=False),
                ex=max(ttl_seconds, 1),
            )
        )
    except Exception:
        return False


def delete_key(key: str) -> bool:
    try:
        return bool(get_redis_client().delete(key))
    except Exception:
        return False


def get_knowledge_base_version() -> str | None:
    try:
        client = get_redis_client()
        client.setnx(KNOWLEDGE_BASE_VERSION_KEY, "1")
        version = client.get(KNOWLEDGE_BASE_VERSION_KEY)
    except Exception:
        return None
    return str(version) if version else None


def refresh_knowledge_base_version() -> str | None:
    try:
        return str(get_redis_client().incr(KNOWLEDGE_BASE_VERSION_KEY))
    except Exception:
        return None
