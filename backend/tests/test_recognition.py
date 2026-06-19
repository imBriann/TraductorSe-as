"""Tests de los filtros anti-spam del Agente de Reconocimiento."""
import pytest

from app.agents.base import AgentContext
from app.agents.recognition import RecognitionAgent
from app.ml.constants import FEATURES_PER_FRAME

FRAME = [0.2] * FEATURES_PER_FRAME


@pytest.mark.asyncio
async def test_motion_gate_ignores_static_hand():
    agent = RecognitionAgent(threshold=0.0)
    # primer frame: se procesa (no hay frame previo con el que comparar)
    ctx1 = AgentContext(raw_sequence=[FRAME], clean_sequence=[FRAME])
    await agent.run(ctx1)
    assert ctx1.accepted is True
    # segundo frame idéntico: la mano no se movió -> se ignora
    ctx2 = AgentContext(raw_sequence=[FRAME], clean_sequence=[FRAME])
    await agent.run(ctx2)
    assert ctx2.accepted is False
    assert ctx2.meta.get("skipped") == "static"


@pytest.mark.asyncio
async def test_confidence_threshold_rejects_low_probability():
    # umbral altísimo: el fallback determinista (prob <= 0.85) no debe pasar
    agent = RecognitionAgent(threshold=0.99)
    ctx = AgentContext(raw_sequence=[FRAME], clean_sequence=[FRAME])
    await agent.run(ctx)
    assert ctx.accepted is False
    assert 0.0 <= ctx.confidence <= 1.0


@pytest.mark.asyncio
async def test_debounce_blocks_repeated_gloss():
    agent = RecognitionAgent(threshold=0.0)
    agent.motion_delta = 0.0  # desactiva el filtro de movimiento para esta prueba
    clean = [[0.2] * FEATURES_PER_FRAME]
    fa = [0.1] * FEATURES_PER_FRAME
    fb = [0.9] * FEATURES_PER_FRAME  # frame distinto => hay movimiento

    ctx_a = AgentContext(raw_sequence=[fa], clean_sequence=clean)
    await agent.run(ctx_a)
    assert ctx_a.accepted is True

    ctx_b = AgentContext(raw_sequence=[fb], clean_sequence=clean)  # misma glosa, movido
    await agent.run(ctx_b)
    assert ctx_b.gloss == ctx_a.gloss
    assert ctx_b.accepted is False
    assert ctx_b.meta.get("skipped") == "debounce"
