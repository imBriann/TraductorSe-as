"""Agente de Preprocesamiento.

Responsabilidades:
  - Normalización de coordenadas (centrado en la muñeca + escala por mano).
  - Filtrado de ruido (descarta frames vacíos / outliers extremos).
  - Suavizado temporal EWMA (Exponentially Weighted Moving Average).
"""
from __future__ import annotations

from typing import List

import numpy as np

from app.agents.base import Agent, AgentContext
from app.core.logging import logger
from app.ml.constants import COORDS_PER_LANDMARK, LANDMARKS_PER_HAND, HANDS


class PreprocessingAgent(Agent):
    name = "preprocessing"

    def __init__(self, ewma_alpha: float = 0.4) -> None:
        # alpha alto => responde rápido; bajo => más suave
        self.alpha = ewma_alpha

    async def run(self, ctx: AgentContext) -> AgentContext:
        frames = ctx.raw_sequence
        if not frames:
            ctx.clean_sequence = []
            return ctx

        normalized = [self._normalize(np.asarray(f, dtype=np.float32)) for f in frames]
        filtered = self._filter_noise(normalized)
        smoothed = self._ewma(filtered)

        ctx.clean_sequence = [v.tolist() for v in smoothed]
        ctx.meta["preprocessing_frames"] = len(ctx.clean_sequence)
        logger.debug("[preprocessing] {} frames procesados", len(ctx.clean_sequence))
        return ctx

    # ---------------------------------------------------- normalización
    @staticmethod
    def _normalize(vec: np.ndarray) -> np.ndarray:
        """Normaliza cada mano: traslada al origen (muñeca) y escala."""
        out = vec.copy().astype(np.float32)
        per_hand = LANDMARKS_PER_HAND * COORDS_PER_LANDMARK
        for h in range(HANDS):
            s = h * per_hand
            e = s + per_hand
            hand = out[s:e].reshape(LANDMARKS_PER_HAND, COORDS_PER_LANDMARK)
            if not np.any(hand):
                continue  # mano ausente
            wrist = hand[0].copy()          # landmark 0 = muñeca
            hand -= wrist                    # centrado
            scale = np.linalg.norm(hand, axis=1).max()
            if scale > 1e-6:
                hand /= scale                # escala invariante al tamaño
            out[s:e] = hand.reshape(-1)
        return out

    # ---------------------------------------------------- filtrado
    @staticmethod
    def _filter_noise(frames: List[np.ndarray]) -> List[np.ndarray]:
        cleaned: List[np.ndarray] = []
        for f in frames:
            f = np.nan_to_num(f, nan=0.0, posinf=0.0, neginf=0.0)
            f = np.clip(f, -5.0, 5.0)  # recorta outliers extremos
            cleaned.append(f)
        return cleaned

    # ---------------------------------------------------- suavizado EWMA
    def _ewma(self, frames: List[np.ndarray]) -> List[np.ndarray]:
        if not frames:
            return frames
        smoothed = [frames[0]]
        for i in range(1, len(frames)):
            prev = smoothed[-1]
            cur = frames[i]
            smoothed.append(self.alpha * cur + (1.0 - self.alpha) * prev)
        return smoothed
