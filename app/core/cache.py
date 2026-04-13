import json

import redis

from app.core.config import get_settings

settings = get_settings()
redis_client = redis.Redis.from_url(settings.redis_url, decode_responses=True)


def acquire_idempotency_key(key: str, ttl_seconds: int = 3600) -> bool:
    try:
        return bool(redis_client.set(name=f"idem:{key}", value="1", ex=ttl_seconds, nx=True))
    except redis.RedisError:
        return True


def set_session_state(session_id: str, payload: dict, ttl_seconds: int = 1800) -> None:
    try:
        redis_client.setex(f"session:{session_id}", ttl_seconds, str(payload))
    except redis.RedisError:
        return


def get_session_state(session_id: str) -> str | None:
    try:
        return redis_client.get(f"session:{session_id}")
    except redis.RedisError:
        return None


def get_cached_json(key: str) -> list | dict | None:
    try:
        cached = redis_client.get(key)
        return json.loads(cached) if cached else None
    except (redis.RedisError, json.JSONDecodeError, TypeError):
        return None


def set_cached_json(key: str, payload: list | dict, ttl_seconds: int) -> None:
    try:
        redis_client.setex(key, ttl_seconds, json.dumps(payload, default=str))
    except redis.RedisError:
        return
