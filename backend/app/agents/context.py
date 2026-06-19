"""Agente de Contexto (Context Agent) — memoria conversacional con KV Cache.

Mantiene el estado de la conversación por sesión en Redis, actuando como una
caché clave-valor (KV Cache) que:

  * recuerda las últimas señas reconocidas         -> ctx:{sk}:glosses   (LIST)
  * mantiene las entidades detectadas (slots)      -> ctx:{sk}:entities  (HASH)
  * conserva las últimas frases generadas          -> ctx:{sk}:history   (LIST)
  * guarda la última frase (para continuaciones)   -> ctx:{sk}:last_text (STRING)
  * cachea el estado KV del modelo Llama (Ollama)  -> ctx:{sk}:ollama_kv (STRING)
  * registra las sesiones activas                  -> ctx:active        (SET)

El contexto se recupera automáticamente ANTES de cada inferencia (`load`) y se
actualiza tras reconocer una seña (`observe`) y tras generar texto (`write_back`).
Tiene persistencia temporal configurable (CONTEXT_TTL_SECONDS) y degrada con
elegancia a un almacén en memoria si Redis no está disponible.
"""
from __future__ import annotations

import json
from typing import Dict, List, Optional

from app.agents.base import Agent, AgentContext
from app.core.config import settings
from app.core.logging import logger
from app.core.redis_client import get_redis
from app.ml.labels import categorize

# Almacén en memoria de respaldo (clave de sesión -> estado)
_MEM: Dict[str, dict] = {}


def _empty_state() -> dict:
    return {"glosses": [], "entities": {}, "history": [], "last_text": None, "ollama_kv": None}


class ContextAgent(Agent):
    name = "context"

    def __init__(self) -> None:
        self.ttl = settings.CONTEXT_TTL_SECONDS
        self.window = settings.HISTORY_WINDOW
        self.max_glosses = settings.MAX_CONTEXT_GLOSSES

    # ------------------------------------------------------ infraestructura
    @staticmethod
    def _keys(sk: str) -> Dict[str, str]:
        return {
            "glosses": f"ctx:{sk}:glosses",
            "entities": f"ctx:{sk}:entities",
            "history": f"ctx:{sk}:history",
            "last_text": f"ctx:{sk}:last_text",
            "ollama_kv": f"ctx:{sk}:ollama_kv",
        }

    async def _redis(self):
        try:
            r = await get_redis()
            if r is None:
                return None
            await r.ping()
            return r
        except Exception:
            return None

    async def _refresh_ttl(self, r, sk: str) -> None:
        for key in self._keys(sk).values():
            try:
                await r.expire(key, self.ttl)
            except Exception:
                pass

    # ------------------------------------------------------ Agent.run
    async def run(self, ctx: AgentContext) -> AgentContext:
        """Por defecto, `run` recupera el contexto (equivalente a `load`)."""
        return await self.load(ctx)

    # ------------------------------------------------------ load
    async def load(self, ctx: AgentContext) -> AgentContext:
        """Recupera el contexto de la sesión y lo inyecta en el AgentContext."""
        sk = ctx.session_key
        if not sk or not ctx.context_enabled:
            return ctx

        r = await self._redis()
        if r is None:
            state = _MEM.setdefault(sk, _empty_state())
            ctx.glosses_buffer = list(state["glosses"])
            ctx.entities = dict(state["entities"])
            ctx.history = list(state["history"])
            ctx.last_text = state["last_text"]
            ctx.ollama_kv = state["ollama_kv"]
            return ctx

        k = self._keys(sk)
        try:
            ctx.glosses_buffer = await r.lrange(k["glosses"], 0, -1)
            ctx.entities = await r.hgetall(k["entities"]) or {}
            ctx.history = await r.lrange(k["history"], 0, -1)
            ctx.last_text = await r.get(k["last_text"])
            raw_kv = await r.get(k["ollama_kv"])
            ctx.ollama_kv = json.loads(raw_kv) if raw_kv else None
            await r.sadd("ctx:active", sk)
        except Exception as exc:  # pragma: no cover
            logger.debug("ContextAgent.load fallo: {}", exc)
        return ctx

    # ------------------------------------------------------ observe
    async def observe(self, ctx: AgentContext) -> AgentContext:
        """Registra una seña recién reconocida en el contexto (si fue aceptada)."""
        sk = ctx.session_key
        if not sk or not ctx.context_enabled or not ctx.accepted or not ctx.gloss:
            return ctx
        gloss = ctx.gloss
        # Evita repetir la misma glosa consecutiva (señal sostenida)
        if ctx.glosses_buffer and ctx.glosses_buffer[-1] == gloss:
            return ctx

        ctx.glosses_buffer.append(gloss)
        if len(ctx.glosses_buffer) > self.max_glosses:
            ctx.glosses_buffer = ctx.glosses_buffer[-self.max_glosses:]

        category = categorize(gloss)
        if category:
            ctx.entities[category] = gloss

        r = await self._redis()
        if r is None:
            state = _MEM.setdefault(sk, _empty_state())
            state["glosses"] = list(ctx.glosses_buffer)
            state["entities"] = dict(ctx.entities)
            return ctx

        k = self._keys(sk)
        try:
            await r.delete(k["glosses"])
            if ctx.glosses_buffer:
                await r.rpush(k["glosses"], *ctx.glosses_buffer)
            if category:
                await r.hset(k["entities"], category, gloss)
            await self._refresh_ttl(r, sk)
        except Exception as exc:  # pragma: no cover
            logger.debug("ContextAgent.observe fallo: {}", exc)
        return ctx

    # ------------------------------------------------------ write_back
    async def write_back(self, ctx: AgentContext) -> AgentContext:
        """Persiste el resultado de la inferencia en la memoria contextual."""
        sk = ctx.session_key
        if not sk or not ctx.context_enabled or not ctx.natural_text:
            return ctx

        ctx.history.append(ctx.natural_text)
        if len(ctx.history) > self.window:
            ctx.history = ctx.history[-self.window:]
        ctx.last_text = ctx.natural_text

        r = await self._redis()
        if r is None:
            state = _MEM.setdefault(sk, _empty_state())
            state["history"] = list(ctx.history)
            state["last_text"] = ctx.last_text
            state["ollama_kv"] = ctx.ollama_kv
            state["glosses"] = []   # la frase se cerró: se vacía el buffer activo
            return ctx

        k = self._keys(sk)
        try:
            await r.delete(k["history"])
            if ctx.history:
                await r.rpush(k["history"], *ctx.history)
            await r.set(k["last_text"], ctx.last_text)
            if ctx.ollama_kv is not None:
                await r.set(k["ollama_kv"], json.dumps(ctx.ollama_kv))
            await r.delete(k["glosses"])  # cierra la frase activa
            await self._refresh_ttl(r, sk)
        except Exception as exc:  # pragma: no cover
            logger.debug("ContextAgent.write_back fallo: {}", exc)
        ctx.glosses_buffer = []
        return ctx

    # ------------------------------------------------------ reset
    async def reset(self, sk: str) -> None:
        """Elimina por completo el contexto de una sesión."""
        if not sk:
            return
        _MEM.pop(sk, None)
        r = await self._redis()
        if r is None:
            return
        try:
            for key in self._keys(sk).values():
                await r.delete(key)
            await r.srem("ctx:active", sk)
        except Exception:  # pragma: no cover
            pass

    async def active_sessions(self) -> List[str]:
        r = await self._redis()
        if r is None:
            return list(_MEM.keys())
        try:
            return list(await r.smembers("ctx:active"))
        except Exception:  # pragma: no cover
            return []
