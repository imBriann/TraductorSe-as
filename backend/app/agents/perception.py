"""Agente de Percepción.

En la arquitectura desplegada, la captura de vídeo y la extracción de
landmarks con MediaPipe Hands ocurren en el navegador (cliente), que envía
los landmarks ya extraídos al backend. Este agente valida y estructura esa
entrada. También ofrece un extractor server-side (extract_from_frame) para
procesar imágenes subidas, usando MediaPipe en el servidor.
"""
from __future__ import annotations

from typing import List

import numpy as np

from app.agents.base import Agent, AgentContext
from app.core.logging import logger
from app.ml.constants import (
    COORDS_PER_LANDMARK,
    FEATURES_PER_FRAME,
    HANDS,
    LANDMARKS_PER_HAND,
)


class PerceptionAgent(Agent):
    name = "perception"

    async def run(self, ctx: AgentContext) -> AgentContext:
        validated: List[List[float]] = []
        for frame in ctx.raw_sequence:
            vec = self._validate_frame(frame)
            if vec is not None:
                validated.append(vec)
        ctx.raw_sequence = validated
        ctx.meta["perception_frames"] = len(validated)
        logger.debug("[perception] {} frames válidos", len(validated))
        return ctx

    @staticmethod
    def _validate_frame(frame: List[float]) -> List[float] | None:
        if not frame:
            return None
        arr = np.asarray(frame, dtype=np.float32)
        arr = np.nan_to_num(arr, nan=0.0, posinf=0.0, neginf=0.0)
        if arr.size == FEATURES_PER_FRAME:
            return arr.tolist()
        # Rellena o recorta a la dimensión esperada
        fixed = np.zeros(FEATURES_PER_FRAME, dtype=np.float32)
        n = min(arr.size, FEATURES_PER_FRAME)
        fixed[:n] = arr[:n]
        return fixed.tolist()

    # ----------------------------------------------------- server-side
    @staticmethod
    def extract_from_frame(image_bgr) -> List[float]:
        """Extrae landmarks de un frame (numpy BGR) usando MediaPipe Hands.

        Devuelve un vector aplanado de tamaño FEATURES_PER_FRAME.
        """
        import cv2  # import perezoso
        import mediapipe as mp

        mp_hands = mp.solutions.hands
        vec = np.zeros(FEATURES_PER_FRAME, dtype=np.float32)
        with mp_hands.Hands(
            static_image_mode=True,
            max_num_hands=HANDS,
            min_detection_confidence=0.5,
        ) as hands:
            rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
            result = hands.process(rgb)
            if result.multi_hand_landmarks:
                for h, hand in enumerate(result.multi_hand_landmarks[:HANDS]):
                    base = h * LANDMARKS_PER_HAND * COORDS_PER_LANDMARK
                    for i, lm in enumerate(hand.landmark):
                        off = base + i * COORDS_PER_LANDMARK
                        vec[off] = lm.x
                        vec[off + 1] = lm.y
                        vec[off + 2] = lm.z
        return vec.tolist()
