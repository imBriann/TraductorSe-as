"""Agente de Reconocimiento.

Ejecuta el modelo Transformer temporal sobre la secuencia limpia y produce una
glosa + confianza. Marca si la predicción supera el umbral (`accepted`); la
acumulación en el buffer la realiza el Context Agent.
"""
from __future__ import annotations

from app.agents.base import Agent, AgentContext
from app.core.config import settings
from app.core.logging import logger
from app.ml.inference import get_engine


class RecognitionAgent(Agent):
    name = "recognition"

    def __init__(self, threshold: float | None = None) -> None:
        self.engine = get_engine()
        self.threshold = threshold if threshold is not None else settings.CONFIDENCE_THRESHOLD

    async def run(self, ctx: AgentContext) -> AgentContext:
        sequence = ctx.clean_sequence or ctx.raw_sequence
        gloss, confidence = self.engine.predict(sequence)
        ctx.gloss = gloss
        ctx.confidence = confidence
        ctx.accepted = confidence >= self.threshold and gloss != "DESCONOCIDO"
        logger.debug(
            "[recognition] gloss={} conf={:.3f} accepted={} (umbral={})",
            gloss, confidence, ctx.accepted, self.threshold,
        )
        return ctx
