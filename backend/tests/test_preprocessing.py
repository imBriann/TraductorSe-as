"""Tests unitarios del Agente de Preprocesamiento (normalización + EWMA)."""
import numpy as np
import pytest

from app.agents.base import AgentContext
from app.agents.preprocessing import PreprocessingAgent
from app.ml.constants import FEATURES_PER_FRAME


@pytest.mark.asyncio
async def test_ewma_smoothing_reduces_variance():
    agent = PreprocessingAgent(ewma_alpha=0.3)
    rng = np.random.default_rng(0)
    noisy = [rng.normal(0.5, 0.2, FEATURES_PER_FRAME).tolist() for _ in range(20)]
    ctx = AgentContext(raw_sequence=noisy)
    ctx = await agent.run(ctx)
    clean = np.asarray(ctx.clean_sequence)
    # La señal suavizada debe tener menor varianza temporal que la original
    assert clean.var(axis=0).mean() <= np.asarray(noisy).var(axis=0).mean()


@pytest.mark.asyncio
async def test_output_length_matches_input():
    agent = PreprocessingAgent()
    seq = [[0.1] * FEATURES_PER_FRAME for _ in range(10)]
    ctx = await agent.run(AgentContext(raw_sequence=seq))
    assert len(ctx.clean_sequence) == 10


def test_normalize_centers_on_wrist():
    agent = PreprocessingAgent()
    vec = np.zeros(FEATURES_PER_FRAME, dtype=np.float32)
    # muñeca de la primera mano en (1,1,1)
    vec[0:3] = [1.0, 1.0, 1.0]
    vec[3:6] = [2.0, 2.0, 2.0]
    out = agent._normalize(vec)
    # tras centrar en la muñeca, el primer punto queda en el origen
    assert np.allclose(out[0:3], [0.0, 0.0, 0.0])
