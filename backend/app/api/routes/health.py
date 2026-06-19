"""Health checks y estado de dependencias."""
from __future__ import annotations

from fastapi import APIRouter

from app.core.redis_client import get_redis
from app.ml.inference import get_engine
from app.services.ollama_service import ollama_service

router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.get("/health/full")
async def health_full():
    # Redis
    redis_ok = False
    try:
        r = await get_redis()
        redis_ok = bool(r and await r.ping())
    except Exception:
        redis_ok = False

    # Ollama
    ollama_ok = await ollama_service.health()

    engine = get_engine()
    return {
        "status": "ok",
        "redis": redis_ok,
        "ollama": ollama_ok,
        "model_trained": engine.trained,
        "num_classes": engine.encoder.num_classes,
    }
