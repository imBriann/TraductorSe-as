"""Tests de integración del pipeline de agentes (sin Ollama ni Redis reales)."""
import pytest

from app.agents.coordinator import CoordinatorAgent
from app.ml.constants import FEATURES_PER_FRAME


@pytest.mark.asyncio
async def test_coordinator_partial_produces_gloss():
    # threshold=0.0 para aceptar la predicción del fallback determinista
    coordinator = CoordinatorAgent(db=None, threshold=0.0)
    seq = [[0.05 * i] * FEATURES_PER_FRAME for i in range(30)]
    ctx = await coordinator.process(
        raw_sequence=seq, device_id=1, session_key="dev1",
        generate_text=False, persist=False, finalize=False,
    )
    assert ctx.gloss is not None
    assert ctx.accepted is True
    assert ctx.glosses_buffer  # la glosa entró al buffer vía Context Agent


@pytest.mark.asyncio
async def test_coordinator_finalize_generates_text():
    coordinator = CoordinatorAgent(db=None, threshold=0.0)
    seq = [[0.2] * FEATURES_PER_FRAME for _ in range(30)]
    ctx = await coordinator.process(
        raw_sequence=seq, device_id=1, session_key="dev-final",
        generate_text=True, persist=False, finalize=True,
    )
    assert ctx.natural_text
    # tras finalizar, el Context Agent guarda la frase en el historial
    assert ctx.history and ctx.history[-1] == ctx.natural_text
