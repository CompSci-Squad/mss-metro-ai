from typing import Any

from pymemcache.client import base

from app.core.settings import settings

_client = base.Client((settings.cache_host, settings.cache_port))


def set_cache(key: str, value: Any, expire: int = 300) -> None:
    _client.set(key, str(value), expire=expire)


def get_cache(key: str) -> str | None:
    val = _client.get(key)
    return val.decode() if val else None
