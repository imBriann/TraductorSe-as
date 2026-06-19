"""Agente Coordinador.

Orquesta el flujo completo del pipeline i5.0:

    Percepción → Preprocesamiento → Reconocimiento → Contexto → Semántico → Persistencia

El Context Agent recupera la memoria conversacional (Redis KV Cache) antes de la
inferencia y la actualiza después, permitiendo traducciones contextuales.
"""
from __future__ import annotations

import time
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base import AgentContext
from app.agents.context import ContextAgent
from app.agents.perception import PerceptionAgent
from app.agents.persistence import PersistenceAgent
from app.agents.preprocessing import PreprocessingAgent
from app.agents.recognition import RecognitionAgent
from app.agents.semantic import SemanticAgent
from app.core.logging import logger


class CoordinatorAgent:
    name = "coordinator"

    def __init__(self, db: Optional[AsyncSession] = None,
                 threshold: float | None = None) -> None:
        self.perception = PerceptionAgent()
        self.preprocessing = PreprocessingAgent()
        self.recognition = RecognitionAgent(threshold=threshold)
        self.context = ContextAgent()
        self.semantic = SemanticAgent()
        self.persistence = PersistenceAgent(db) if db is not None else None

    async def reset_context(self, session_key: str) -> None:
        await self.context.reset(session_key)

    async def process(
        self,
        raw_sequence: List[List[float]],
        device_id: Optional[int] = None,
        session_key: str = "",
        session_id: Optional[int] = None,
        generate_text: bool = True,
        context_enabled: bool = True,
        persist: bool = True,
        finalize: bool = False,
    ) -> AgentContext:
        """Procesa un fragmento de secuencia.

        - finalize=True genera la frase (con contexto) + persiste y cierra el
          buffer activo de la sesión.
        """
        t0 = time.perf_counter()

        ctx = AgentContext(
            raw_sequence=raw_sequence,
            device_id=device_id,
            session_key=session_key or (f"dev{device_id}" if device_id else ""),
            session_id=session_id,
            generate_text=generate_text,
            context_enabled=context_enabled,
        )

        # 1) Percepción 2) Preprocesamiento 3) Reconocimiento
        ctx = await self.perception.run(ctx)
        ctx = await self.preprocessing.run(ctx)
        ctx = await self.recognition.run(ctx)

        # 4) Contexto: recupera memoria y registra la seña reconocida
        ctx = await self.context.load(ctx)
        ctx = await self.context.observe(ctx)

        # 5) Semántico + 6) Persistencia (solo al finalizar la frase)
        if finalize and ctx.glosses_buffer:
            ctx.generate_text = True
            ctx = await self.semantic.run(ctx)

            if persist and self.persistence is not None:
                ctx.latency_ms = int((time.perf_counter() - t0) * 1000)
                await self.persistence.run(ctx)

            # Context Agent escribe el resultado y cierra el buffer
            ctx = await self.context.write_back(ctx)

        ctx.latency_ms = ctx.latency_ms or int((time.perf_counter() - t0) * 1000)
        logger.debug(
            "[coordinator] gloss={} buffer={} entities={} finalize={} {}ms",
            ctx.gloss, ctx.glosses_buffer, ctx.entities, finalize, ctx.latency_ms,
        )
        return ctx
