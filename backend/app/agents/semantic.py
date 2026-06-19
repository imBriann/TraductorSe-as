"""Agente Semántico.

Convierte el buffer de glosas en una frase natural en español usando Llama 3.1
(vía Ollama), **considerando el contexto** recuperado por el Context Agent
(historial de frases, entidades activas y KV cache del modelo).
"""
from __future__ import annotations

from app.agents.base import Agent, AgentContext
from app.core.logging import logger
from app.services.ollama_service import ollama_service


class SemanticAgent(Agent):
    name = "semantic"

    async def run(self, ctx: AgentContext) -> AgentContext:
        if not ctx.generate_text or not ctx.glosses_buffer:
            return ctx

        text, new_kv = await ollama_service.glosses_to_text(
            glosses=ctx.glosses_buffer,
            history=ctx.history if ctx.context_enabled else [],
            entities=ctx.entities if ctx.context_enabled else {},
            kv=ctx.ollama_kv if ctx.context_enabled else None,
        )
        ctx.natural_text = text
        ctx.ollama_kv = new_kv
        ctx.used_context = bool(ctx.context_enabled and (ctx.history or ctx.entities))
        logger.debug(
            "[semantic] texto='{}' (contexto={})", text, ctx.used_context
        )
        return ctx
