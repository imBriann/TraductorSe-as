"""Contrato base de los agentes i5.0 y contexto compartido del pipeline."""
from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class AgentContext:
    """Estado que fluye entre agentes durante una interpretación."""

    # Entrada cruda (frames de landmarks aplanados)
    raw_sequence: List[List[float]] = field(default_factory=list)
    # Secuencia normalizada/suavizada
    clean_sequence: List[List[float]] = field(default_factory=list)

    # Resultado de reconocimiento
    gloss: Optional[str] = None
    confidence: float = 0.0
    accepted: bool = False  # ¿supera el umbral de confianza?

    # Buffer de glosas activas (frase en construcción)
    glosses_buffer: List[str] = field(default_factory=list)

    # ---- Memoria contextual (gestionada por el Context Agent / Redis) ----
    history: List[str] = field(default_factory=list)        # frases previas
    entities: Dict[str, str] = field(default_factory=dict)  # slots conversacionales
    last_text: Optional[str] = None                          # última frase generada
    ollama_kv: Optional[list] = None                         # KV cache de Ollama
    used_context: bool = False

    # Resultado semántico
    natural_text: Optional[str] = None

    # Metadatos
    device_id: Optional[int] = None
    session_key: str = ""              # clave de la conversación en Redis
    session_id: Optional[int] = None   # id de sesión persistida (opcional)
    generate_text: bool = True
    context_enabled: bool = True
    latency_ms: int = 0
    meta: Dict[str, Any] = field(default_factory=dict)


class Agent(abc.ABC):
    """Interfaz de un agente. Cada agente transforma el contexto."""

    name: str = "agent"

    @abc.abstractmethod
    async def run(self, ctx: AgentContext) -> AgentContext:  # pragma: no cover
        ...
