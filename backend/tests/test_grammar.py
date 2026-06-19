"""Tests del compositor gramatical contextual (NLG por reglas)."""
import unicodedata

from app.services.grammar import compose


def _nfc(s):
    return unicodedata.normalize("NFC", s) if s else s


def test_present_tense_sentence():
    assert _nfc(compose(["YO", "ESTUDIAR", "UNIVERSIDAD"], {})) == _nfc("Estudio en la universidad.")


def test_contextual_future_with_time_marker():
    # Caso objetivo del proyecto: MAÑANA + contexto previo (entidades)
    out = compose(["MAÑANA"], {"subject": "YO", "verb": "ESTUDIAR", "place": "UNIVERSIDAD"})
    assert _nfc(out) == _nfc("Mañana estudiaré en la universidad.")


def test_verb_ir_uses_preposition_a():
    out = compose(["MAÑANA"], {"verb": "IR", "place": "UNIVERSIDAD"})
    assert _nfc(out) == _nfc("Mañana iré a la universidad.")


def test_past_tense():
    out = compose(["AYER"], {"verb": "COMER", "place": "CASA"})
    assert _nfc(out) == _nfc("Ayer comí en casa.")


def test_standalone_greeting():
    assert _nfc(compose(["HOLA"], {})) == _nfc("Hola.")


def test_unknown_returns_none():
    assert compose(["DESCONOCIDO"], {}) is None
