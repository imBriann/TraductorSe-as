from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class InferenceRequest(BaseModel):
    """Petición de inferencia: secuencia de frames de landmarks.

    Cada frame es una lista de floats (landmarks aplanados x,y,z por mano).
    """
    sequence: List[List[float]] = Field(
        ..., description="Secuencia temporal de vectores de landmarks normalizados"
    )
    session_id: Optional[int] = None
    generate_text: bool = True


class InferenceResult(BaseModel):
    gloss: str
    confidence: float
    glosses_buffer: List[str] = []
    natural_text: Optional[str] = None
    entities: Dict[str, str] = {}
    history: List[str] = []
    used_context: bool = False
    latency_ms: int = 0


class TranslationCreate(BaseModel):
    glosses: List[str]
    natural_text: str = ""
    confidence: float = 0.0
    latency_ms: int = 0
    session_id: Optional[int] = None
    source: str = "realtime"
    used_context: bool = False


class TranslationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    glosses: List[str]
    natural_text: str
    confidence: float
    latency_ms: int
    source: str
    used_context: bool
    session_id: Optional[int]
    created_at: datetime


class SessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    total_signs: int
    started_at: datetime
    ended_at: Optional[datetime]
