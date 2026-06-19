from __future__ import annotations

from typing import Dict, List

from pydantic import BaseModel


class StatsSummary(BaseModel):
    total_translations: int
    total_sessions: int
    avg_confidence: float
    avg_latency_ms: float
    top_glosses: List[Dict[str, object]]
    translations_per_day: List[Dict[str, object]]


class SystemInfo(BaseModel):
    app_name: str
    version: str
    environment: str
    dev_mode: bool
    model_trained: bool
    num_classes: int
    sequence_length: int
    confidence_threshold: float
    context_ttl_seconds: int
    redis_ok: bool
    ollama_ok: bool
    pipeline: List[str]
