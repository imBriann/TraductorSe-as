"""Información del sistema y estado de dependencias."""
from __future__ import annotations

from fastapi import APIRouter

from app import __version__
from app.core.config import settings
from app.core.redis_client import get_redis
from app.ml.inference import get_engine
from app.schemas.stats import SystemInfo
from app.services.ollama_service import ollama_service

router = APIRouter(prefix="/system", tags=["system"])

PIPELINE = [
    "Camera", "MediaPipe", "Perception", "Preprocessing",
    "Recognition", "Context", "Semantic (Llama 3.1)", "Persistence", "Frontend",
]


@router.get("/info", response_model=SystemInfo)
async def system_info():
    redis_ok = False
    try:
        r = await get_redis()
        redis_ok = bool(r and await r.ping())
    except Exception:
        redis_ok = False

    ollama_ok = await ollama_service.health()
    engine = get_engine()

    return SystemInfo(
        app_name=settings.APP_NAME,
        version=__version__,
        environment=settings.APP_ENV,
        dev_mode=settings.DEV_MODE,
        model_trained=engine.trained,
        num_classes=engine.encoder.num_classes,
        sequence_length=settings.SEQUENCE_LENGTH,
        confidence_threshold=settings.CONFIDENCE_THRESHOLD,
        context_ttl_seconds=settings.CONTEXT_TTL_SECONDS,
        redis_ok=redis_ok,
        ollama_ok=ollama_ok,
        pipeline=PIPELINE,
    )
