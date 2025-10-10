"""Redis cache - funções simples."""

import json
from typing import Any

import redis

from app.core.logger import logger
from app.core.settings import settings

# Cliente global
_redis_client = None


def _get_client() -> redis.Redis:
    """Retorna cliente Redis (singleton)."""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            password=settings.redis_password or None,
            decode_responses=True,
        )
        logger.info("redis_connected")
    return _redis_client


def get(key: str) -> str | None:
    """Busca valor no cache."""
    try:
        return _get_client().get(key)
    except Exception as e:
        logger.error("cache_get_error", key=key, error=str(e))
        return None


def set(key: str, value: str, ttl: int = 3600) -> bool:
    """Salva valor no cache."""
    try:
        _get_client().setex(key, ttl, value)
        return True
    except Exception as e:
        logger.error("cache_set_error", key=key, error=str(e))
        return False


def delete(key: str) -> bool:
    """Remove chave do cache."""
    try:
        _get_client().delete(key)
        return True
    except Exception as e:
        logger.error("cache_delete_error", key=key, error=str(e))
        return False


def get_json(key: str) -> Any | None:
    """Busca e deserializa JSON."""
    value = get(key)
    if value:
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return None
    return None


def set_json(key: str, value: Any, ttl: int = 3600) -> bool:
    """Serializa e salva JSON."""
    try:
        return set(key, json.dumps(value), ttl)
    except (TypeError, ValueError):
        return False
