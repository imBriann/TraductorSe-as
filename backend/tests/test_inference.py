"""Tests del motor de inferencia y del modelo Transformer."""
import torch

from app.ml.constants import FEATURES_PER_FRAME
from app.ml.inference import get_engine
from app.ml.labels import LabelEncoder, DEFAULT_LABELS
from app.ml.model import build_model


def test_label_encoder_roundtrip():
    enc = LabelEncoder(DEFAULT_LABELS)
    for i, lab in enumerate(DEFAULT_LABELS):
        assert enc.encode(lab) == i
        assert enc.decode(i) == lab


def test_model_forward_shape():
    model = build_model(num_classes=5)
    x = torch.randn(2, 30, FEATURES_PER_FRAME)
    mask = torch.zeros(2, 30, dtype=torch.bool)
    out = model(x, mask)
    assert out.shape == (2, 5)


def test_engine_predict_returns_label_and_confidence():
    engine = get_engine()
    seq = [[0.01 * i] * FEATURES_PER_FRAME for i in range(30)]
    gloss, conf = engine.predict(seq)
    assert isinstance(gloss, str)
    assert 0.0 <= conf <= 1.0


def test_engine_predict_is_deterministic_in_fallback():
    engine = get_engine()
    seq = [[0.2] * FEATURES_PER_FRAME for _ in range(30)]
    a = engine.predict(seq)
    b = engine.predict(seq)
    assert a == b
