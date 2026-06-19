"""Agente de Reconocimiento.

Ejecuta el modelo temporal sobre la secuencia limpia y produce una glosa +
probabilidad. Aplica tres filtros anti-spam ANTES de aceptar una seña, para
evitar falsos positivos cuando la mano está quieta o cuando se repite la misma
palabra en cada frame del bucle:

  1. Filtro de movimiento (delta): si los landmarks apenas cambian respecto al
     frame anterior, se considera la mano estática y NO se ejecuta el modelo.
  2. Umbral de confianza: solo se acepta si la probabilidad supera el umbral
     (por defecto 0.85).
  3. Debounce temporal: bloquea repetir la MISMA glosa durante DEBOUNCE_SECONDS.

El estado (frame previo, última glosa y su instante) se conserva en la instancia
del agente, que el Coordinador reutiliza durante toda una conexión en tiempo real.
"""
from __future__ import annotations

import time

import numpy as np

from app.agents.base import Agent, AgentContext
from app.core.config import settings
from app.core.logging import logger
from app.ml.inference import get_engine


class RecognitionAgent(Agent):
    name = "recognition"

    def __init__(self, threshold: float | None = None) -> None:
        self.engine = get_engine()
        self.threshold = threshold if threshold is not None else settings.CONFIDENCE_THRESHOLD
        self.debounce_seconds = settings.DEBOUNCE_SECONDS
        self.motion_delta = settings.MOTION_DELTA_THRESHOLD

        # Estado entre frames (persiste mientras viva el agente: p. ej. una conexión WS)
        self._prev_frame: np.ndarray | None = None
        self._last_gloss: str | None = None
        self._last_emit: float = 0.0

    # ------------------------------------------------- filtro de movimiento
    def _is_static(self, ctx: AgentContext) -> bool:
        seq = ctx.raw_sequence
        if not seq:
            return True
        current = np.asarray(seq[-1], dtype=np.float32)
        prev = self._prev_frame
        self._prev_frame = current
        if prev is None or prev.shape != current.shape:
            return False  # primer frame: aún no se puede medir movimiento
        delta = float(np.mean(np.abs(current - prev)))
        ctx.meta["motion_delta"] = round(delta, 5)
        return delta < self.motion_delta

    # ----------------------------------------------------------------- run
    async def run(self, ctx: AgentContext) -> AgentContext:
        # (1) Movimiento estático -> no gastamos cómputo en el modelo
        if self._is_static(ctx):
            ctx.gloss = None
            ctx.confidence = 0.0
            ctx.accepted = False
            ctx.meta["skipped"] = "static"
            logger.debug("[recognition] frame estático ignorado (delta<{})", self.motion_delta)
            return ctx

        sequence = ctx.clean_sequence or ctx.raw_sequence
        gloss, confidence = self.engine.predict(sequence)
        ctx.gloss = gloss
        ctx.confidence = confidence

        # (2) Umbral de confianza
        accepted = confidence >= self.threshold and gloss != "DESCONOCIDO"

        # (3) Debounce temporal: misma glosa repetida demasiado pronto
        now = time.monotonic()
        if accepted and gloss == self._last_gloss and (now - self._last_emit) < self.debounce_seconds:
            accepted = False
            ctx.meta["skipped"] = "debounce"

        ctx.accepted = accepted
        if accepted:
            self._last_gloss = gloss
            self._last_emit = now

        logger.debug(
            "[recognition] gloss={} prob={:.3f} accepted={} (umbral={}, debounce={}s)",
            gloss, confidence, accepted, self.threshold, self.debounce_seconds,
        )
        return ctx
