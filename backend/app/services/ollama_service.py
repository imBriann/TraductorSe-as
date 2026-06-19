"""Cliente del Agente Semántico hacia Llama 3.1 vía Ollama.

Convierte glosas LSC en una frase natural en español **considerando el contexto
previo** de la conversación. Reutiliza el array `context` que devuelve Ollama
(su estado KV) para mantener coherencia y reducir latencia entre señas de la
misma sesión. Incluye fallback gramatical local si Ollama no está disponible.
"""
from __future__ import annotations

import time
from typing import Dict, List, Optional, Tuple

import httpx

from app.core.config import settings
from app.core.logging import logger
from app.services import grammar

# Tras un fallo de conexión, se evita reintentar Ollama durante este lapso
# (circuit breaker) para que el fallback gramatical sea instantáneo en tiempo real.
_DOWN_COOLDOWN_SECONDS = 30
_CONNECT_TIMEOUT_SECONDS = 3.0

SYSTEM_PROMPT = (
    "Eres un traductor experto de Lengua de Señas Colombiana (LSC) al español "
    "escrito. Recibes GLOSAS (palabras clave en mayúsculas, sin conjugar ni "
    "conectores) y, opcionalmente, el CONTEXTO de la conversación (frases previas "
    "y entidades activas). Tu tarea es producir UNA sola oración natural, "
    "gramaticalmente correcta, en español neutro de Colombia, que integre las "
    "nuevas glosas con el contexto. Si las nuevas glosas continúan o modifican la "
    "idea previa (por ejemplo un marcador temporal como MAÑANA), refléjalo en el "
    "tiempo verbal y la construcción. No expliques nada ni uses comillas: responde "
    "únicamente con la oración final."
)

FEW_SHOT = (
    "Glosas: YO IR UNIVERSIDAD MAÑANA\n"
    "Oración: Mañana voy a la universidad.\n\n"
    "Contexto previo: \"Yo estudio en la universidad.\" | entidades: verbo=ESTUDIAR, lugar=UNIVERSIDAD\n"
    "Glosas: MAÑANA\n"
    "Oración: Mañana estudiaré en la universidad.\n\n"
)


class OllamaService:
    def __init__(self) -> None:
        self.host = settings.OLLAMA_HOST.rstrip("/")
        self.model = settings.OLLAMA_MODEL
        self.timeout = settings.OLLAMA_TIMEOUT
        self._down_until = 0.0  # circuit breaker

    async def _generate(self, prompt: str, kv: Optional[list]) -> Tuple[str, Optional[list]]:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": SYSTEM_PROMPT,
            "stream": False,
            "options": {"temperature": 0.3, "top_p": 0.9},
        }
        if kv:
            # Reutiliza el estado KV del modelo de la inferencia previa
            payload["context"] = kv
        timeout = httpx.Timeout(self.timeout, connect=_CONNECT_TIMEOUT_SECONDS)
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(f"{self.host}/api/generate", json=payload)
            resp.raise_for_status()
            data = resp.json()
            return (data.get("response") or "").strip(), data.get("context")

    @staticmethod
    def _build_prompt(
        glosses: List[str], history: List[str], entities: Dict[str, str]
    ) -> str:
        parts = [FEW_SHOT]
        if history:
            previas = " ".join(f'"{h}"' for h in history[-3:])
            parts.append(f"Contexto previo: {previas}\n")
        if entities:
            ents = ", ".join(f"{k}={v}" for k, v in entities.items())
            parts.append(f"Entidades activas: {ents}\n")
        parts.append(f"Glosas: {' '.join(glosses)}\nOración:")
        return "".join(parts)

    async def glosses_to_text(
        self,
        glosses: List[str],
        history: Optional[List[str]] = None,
        entities: Optional[Dict[str, str]] = None,
        kv: Optional[list] = None,
    ) -> Tuple[str, Optional[list]]:
        """Devuelve (texto_natural, nuevo_kv)."""
        if not glosses:
            return "", kv
        history = history or []
        entities = entities or {}

        # Desactivado por configuración (p. ej. Railway sin Ollama) -> fallback directo.
        if not settings.OLLAMA_ENABLED:
            return self._local_fallback(glosses, entities), kv

        # Circuit breaker: si Ollama falló hace poco, no esperamos; vamos al fallback.
        if time.monotonic() < self._down_until:
            return self._local_fallback(glosses, entities), kv

        prompt = self._build_prompt(glosses, history, entities)
        try:
            text, new_kv = await self._generate(prompt, kv)
            if text:
                return text.splitlines()[0].strip().strip('"'), new_kv
        except Exception as exc:  # pragma: no cover
            self._down_until = time.monotonic() + _DOWN_COOLDOWN_SECONDS
            logger.warning(
                "Ollama no disponible ({}). Fallback gramatical activado {}s.",
                exc, _DOWN_COOLDOWN_SECONDS,
            )
        return self._local_fallback(glosses, entities), kv

    @staticmethod
    def _local_fallback(glosses: List[str], entities: Dict[str, str]) -> str:
        """Composición gramatical contextual sin LLM (degradación elegante).

        Usa el compositor basado en reglas (entidades + tiempo verbal); si no
        cubre las glosas, une las palabras de forma simple.
        """
        composed = grammar.compose(glosses, entities)
        if composed:
            return composed
        words = [g.replace("_", " ").lower() for g in glosses]
        sentence = " ".join(words).strip()
        if sentence:
            sentence = sentence[0].upper() + sentence[1:]
            if not sentence.endswith((".", "?", "!")):
                sentence += "."
        return sentence

    async def health(self) -> bool:
        if not settings.OLLAMA_ENABLED:
            return False
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{self.host}/api/tags")
                return resp.status_code == 200
        except Exception:
            return False


ollama_service = OllamaService()
