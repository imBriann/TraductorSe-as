"""Tests del Context Agent (memoria contextual / KV Cache, fallback en memoria)."""
import pytest

from app.agents.base import AgentContext
from app.agents.context import ContextAgent, _MEM


@pytest.fixture(autouse=True)
def _clear_mem():
    _MEM.clear()
    yield
    _MEM.clear()


@pytest.mark.asyncio
async def test_observe_adds_gloss_and_entity():
    agent = ContextAgent()
    ctx = AgentContext(session_key="s1", gloss="YO", confidence=0.9, accepted=True)
    await agent.load(ctx)
    await agent.observe(ctx)
    assert ctx.glosses_buffer == ["YO"]
    assert ctx.entities.get("subject") == "YO"


@pytest.mark.asyncio
async def test_no_duplicate_consecutive_gloss():
    agent = ContextAgent()
    for _ in range(3):
        ctx = AgentContext(session_key="s2", gloss="UNIVERSIDAD", confidence=0.9, accepted=True)
        await agent.load(ctx)
        await agent.observe(ctx)
    assert ctx.glosses_buffer == ["UNIVERSIDAD"]
    assert ctx.entities.get("place") == "UNIVERSIDAD"


@pytest.mark.asyncio
async def test_write_back_persists_history_and_clears_buffer():
    agent = ContextAgent()
    ctx = AgentContext(session_key="s3", gloss="ESTUDIAR", confidence=0.9, accepted=True)
    await agent.load(ctx)
    await agent.observe(ctx)
    ctx.natural_text = "Yo estudio en la universidad."
    await agent.write_back(ctx)

    # Nueva inferencia recupera el contexto previo
    ctx2 = AgentContext(session_key="s3", gloss="MAÑANA", confidence=0.9, accepted=True)
    await agent.load(ctx2)
    assert ctx2.history == ["Yo estudio en la universidad."]
    assert ctx2.last_text == "Yo estudio en la universidad."
    assert ctx2.entities.get("verb") == "ESTUDIAR"  # entidades persisten
    assert ctx2.glosses_buffer == []                # el buffer se vació


@pytest.mark.asyncio
async def test_reset_clears_context():
    agent = ContextAgent()
    ctx = AgentContext(session_key="s4", gloss="YO", confidence=0.9, accepted=True)
    await agent.load(ctx)
    await agent.observe(ctx)
    await agent.reset("s4")
    ctx2 = AgentContext(session_key="s4")
    await agent.load(ctx2)
    assert ctx2.glosses_buffer == []
    assert ctx2.entities == {}
