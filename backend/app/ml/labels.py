"""Gestión del vocabulario de señas (etiquetas <-> índices) y categorías de entidad."""
from __future__ import annotations

import json
import os
from typing import Dict, List, Optional

# Vocabulario LSC por defecto (ampliable vía data/labels.json o entrenamiento).
DEFAULT_LABELS: List[str] = [
    "HOLA", "GRACIAS", "POR_FAVOR", "SI", "NO", "YO", "TU",
    "IR", "COMER", "BEBER", "ESTUDIAR", "CASA", "UNIVERSIDAD", "TRABAJO",
    "HOY", "MAÑANA", "AYER", "BIEN", "MAL", "AYUDA", "NOMBRE",
]

# Clasificación ligera de glosas en categorías de entidad. La usa el Context
# Agent para mantener los "slots" de la conversación (sujeto, verbo, lugar, tiempo).
GLOSS_CATEGORY: Dict[str, str] = {
    # Sujetos / pronombres
    "YO": "subject", "TU": "subject", "EL": "subject", "ELLA": "subject",
    "NOSOTROS": "subject",
    # Verbos
    "IR": "verb", "COMER": "verb", "BEBER": "verb", "ESTUDIAR": "verb",
    "TRABAJAR": "verb", "AYUDAR": "verb", "QUERER": "verb",
    # Lugares / objetos
    "CASA": "place", "UNIVERSIDAD": "place", "TRABAJO": "place",
    # Marcadores temporales
    "HOY": "time", "MAÑANA": "time", "AYER": "time",
    # Cortesía / interjecciones
    "HOLA": "greeting", "GRACIAS": "courtesy", "POR_FAVOR": "courtesy",
    "SI": "modifier", "NO": "modifier", "BIEN": "modifier", "MAL": "modifier",
}


def categorize(gloss: str) -> Optional[str]:
    """Devuelve la categoría de entidad de una glosa, o None si es desconocida."""
    return GLOSS_CATEGORY.get(gloss)


class LabelEncoder:
    def __init__(self, labels: List[str]) -> None:
        self.labels = list(labels)
        self.label_to_idx = {l: i for i, l in enumerate(self.labels)}

    @property
    def num_classes(self) -> int:
        return len(self.labels)

    def encode(self, label: str) -> int:
        return self.label_to_idx[label]

    def decode(self, idx: int) -> str:
        if 0 <= idx < len(self.labels):
            return self.labels[idx]
        return "DESCONOCIDO"

    def save(self, path: str) -> None:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump({"labels": self.labels}, fh, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, path: str) -> "LabelEncoder":
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            return cls(data.get("labels", DEFAULT_LABELS))
        return cls(DEFAULT_LABELS)
