"""Test del Agente Semántico en modo offline (fallback gramatical contextual).

Verifica el flujo conversacional de dos turnos a través del Context Agent +
Semantic Agent sin Ollama ni Redis (almacén en memoria).
"""
import unicodedata

import pytest

from app.agents.base import AgentContext
from app.agents.context import ContextAgent, _MEM
from app.agents.semantic import SemanticAgent
from app.services import ollama_service as ollama_mod


def _nfc(s):
    return unicodedata.normalize("NFC", s) if s else s


@pytest.fixture(autouse=True)
def _offline_and_clear(monkeypatch):
    async def _raise(*args, **kwargs):
        raise ConnectionError("offline")
    monkeypatch.setattr(ollama_mod.ollama_service, "_generate", _raise)
    _MEM.clear()
    yield
    _MEM.clear()


async def _turn(context, semantic, sk, glosses):
    ctx = AgentContext(session_key=sk, context_enabled=True)
    for g in glosses:
        ctx.gloss = g
        ctx.accepted = True
        await context.load(ctx)
        await context.observe(ctx)
    ctx.generate_text = True
    await semantic.run(ctx)
    await context.write_back(ctx)
    return ctx


@pytest.mark.asyncio
async def test_two_turn_contextual_translation():
    context = ContextAgent()
    semantic = SemanticAgent()
    sk = "sem-demo"

    t1 = await _turn(context, semantic, sk, ["YO", "ESTUDIAR", "UNIVERSIDAD"])
    assert _nfc(t1.natural_text) == _nfc("Estudio en la universidad.")

    t2 = await _turn(context, semantic, sk, ["MAÑANA"])
    # El contexto previo (verbo + lugar) se integra con la nueva glosa temporal
    assert _nfc(t2.natural_text) == _nfc("Mañana estudiaré en la universidad.")
    assert t2.used_context is True
