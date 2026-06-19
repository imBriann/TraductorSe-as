"""Cliente Redis asíncrono compartido para caché y métricas en vivo."""
from __future__ import annotations

from typing import Optional

import redis.asyncio as aioredis

from app.core.config import settings
from app.core.logging import logger

_redis: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    """Devuelve (creando si hace falta) el cliente Redis singleton."""
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
        try:
            await _redis.ping()
            logger.info("Conexión a Redis establecida")
        except Exception as exc:  # pragma: no cover
            logger.warning("Redis no disponible: {}", exc)
    return _redis


async def close_redis() -> None:
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None
