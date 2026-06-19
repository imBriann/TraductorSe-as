"""Agente de Persistencia.

Guarda traducciones y métricas en PostgreSQL y actualiza contadores en vivo en
Redis. Asocia los datos al dispositivo anónimo (no a un usuario autenticado).
"""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base import Agent, AgentContext
from app.core.logging import logger
from app.core.redis_client import get_redis
from app.crud import translation as crud_tr
from app.models.metric import UsageMetric
from app.schemas.translation import TranslationCreate


class PersistenceAgent(Agent):
    name = "persistence"

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def run(self, ctx: AgentContext) -> AgentContext:
        if ctx.device_id is None or not ctx.natural_text:
            return ctx

        data = TranslationCreate(
            glosses=list(ctx.glosses_buffer),
            natural_text=ctx.natural_text or "",
            confidence=ctx.confidence,
            latency_ms=ctx.latency_ms,
            session_id=ctx.session_id,
            source=ctx.meta.get("source", "realtime"),
            used_context=ctx.used_context,
        )
        tr = await crud_tr.create_translation(self.db, ctx.device_id, data)

        metric = UsageMetric(
            device_id=ctx.device_id,
            event="translation",
            value=1.0,
            avg_confidence=ctx.confidence,
            avg_latency_ms=float(ctx.latency_ms),
        )
        self.db.add(metric)
        await self.db.flush()

        ctx.meta["translation_id"] = tr.id

        try:
            redis = await get_redis()
            if redis is not None:
                await redis.incr("metrics:translations:total")
        except Exception as exc:  # pragma: no cover
            logger.debug("Redis incr falló: {}", exc)

        logger.debug("[persistence] traducción {} guardada", tr.id)
        return ctx
