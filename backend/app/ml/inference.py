"""Motor de inferencia: carga el Transformer y clasifica secuencias de landmarks.

Si no existe un checkpoint entrenado, opera en modo *fallback* determinista
(útil para desarrollo, demos y tests) sin romper el flujo de la aplicación.
"""
from __future__ import annotations

import os
import threading
from typing import List, Tuple

import numpy as np
import torch

from app.core.config import settings
from app.core.logging import logger
from app.ml.constants import FEATURES_PER_FRAME
from app.ml.labels import LabelEncoder
from app.ml.model import build_model


class InferenceEngine:
    _instance: "InferenceEngine | None" = None
    _lock = threading.Lock()

    def __init__(self) -> None:
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.encoder = LabelEncoder.load(settings.LABELS_PATH)
        self.seq_len = settings.SEQUENCE_LENGTH
        self.model = None
        self.trained = False
        self._load()

    # --------------------------------------------------------- singleton
    @classmethod
    def instance(cls) -> "InferenceEngine":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    # --------------------------------------------------------- carga
    def _load(self) -> None:
        self.model = build_model(num_classes=self.encoder.num_classes)
        if os.path.exists(settings.MODEL_PATH):
            try:
                ckpt = torch.load(settings.MODEL_PATH, map_location=self.device)
                state = ckpt.get("model_state", ckpt)
                if "labels" in ckpt:
                    self.encoder = LabelEncoder(ckpt["labels"])
                    self.model = build_model(num_classes=self.encoder.num_classes)
                self.model.load_state_dict(state)
                self.trained = True
                logger.info(
                    "Modelo Transformer cargado desde {} ({} clases)",
                    settings.MODEL_PATH, self.encoder.num_classes,
                )
            except Exception as exc:  # pragma: no cover
                logger.warning("No se pudo cargar el checkpoint: {}. Modo fallback.", exc)
        else:
            logger.warning(
                "No existe checkpoint en {}. Operando en modo fallback determinista.",
                settings.MODEL_PATH,
            )
        self.model.to(self.device)
        self.model.eval()

    # --------------------------------------------------------- helpers
    def _prepare(self, sequence: List[List[float]]) -> Tuple[torch.Tensor, torch.Tensor]:
        """Convierte la secuencia en tensores [1, T, F] + máscara de padding."""
        arr = np.asarray(sequence, dtype=np.float32)
        if arr.ndim == 1:
            arr = arr.reshape(1, -1)
        # Ajusta dimensión de características
        if arr.shape[1] != FEATURES_PER_FRAME:
            fixed = np.zeros((arr.shape[0], FEATURES_PER_FRAME), dtype=np.float32)
            n = min(arr.shape[1], FEATURES_PER_FRAME)
            fixed[:, :n] = arr[:, :n]
            arr = fixed

        T = arr.shape[0]
        mask = np.zeros((self.seq_len,), dtype=bool)
        if T >= self.seq_len:
            arr = arr[-self.seq_len:]
        else:
            pad = np.zeros((self.seq_len - T, FEATURES_PER_FRAME), dtype=np.float32)
            arr = np.concatenate([arr, pad], axis=0)
            mask[T:] = True  # marcar padding

        x = torch.from_numpy(arr).unsqueeze(0).to(self.device)        # [1, T, F]
        m = torch.from_numpy(mask).unsqueeze(0).to(self.device)       # [1, T]
        return x, m

    # --------------------------------------------------------- predict
    @torch.no_grad()
    def predict(self, sequence: List[List[float]]) -> Tuple[str, float]:
        if not sequence:
            return "DESCONOCIDO", 0.0

        if self.trained and self.model is not None:
            x, mask = self._prepare(sequence)
            logits = self.model(x, mask)
            probs = torch.softmax(logits, dim=-1).squeeze(0)
            conf, idx = torch.max(probs, dim=-1)
            return self.encoder.decode(int(idx.item())), float(conf.item())

        return self._fallback(sequence)

    def _fallback(self, sequence: List[List[float]]) -> Tuple[str, float]:
        """Heurística determinista basada en el hash del movimiento agregado.

        Garantiza salidas estables y reproducibles sin modelo entrenado.
        """
        arr = np.asarray(sequence, dtype=np.float32)
        signature = float(np.nan_to_num(arr).sum())
        idx = abs(int(signature * 1000)) % self.encoder.num_classes
        # confianza simulada por debajo del umbral real para no contaminar métricas
        conf = 0.55 + (abs(signature) % 0.3)
        return self.encoder.decode(idx), round(min(conf, 0.85), 4)


def get_engine() -> InferenceEngine:
    return InferenceEngine.instance()
