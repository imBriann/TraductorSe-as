"""Compositor gramatical local (NLG basado en reglas).

Sirve de *fallback* contextual del Agente Semántico cuando Llama 3.1 (Ollama) no
está disponible: combina las glosas actuales con las entidades acumuladas por el
Context Agent y produce una oración natural en español, ajustando el tiempo
verbal según el marcador temporal detectado.

Cubre el vocabulario LSC por defecto; para glosas fuera de cobertura degrada a
una unión simple de palabras.
"""
from __future__ import annotations

import unicodedata
from typing import Dict, List, Optional

from app.ml.labels import categorize

# Marcador temporal -> (palabra inicial, tiempo verbal)
TIME = {
    "HOY": ("Hoy", "pres"),
    "MAÑANA": ("Mañana", "fut"),
    "AYER": ("Ayer", "past"),
}

# Conjugaciones por sujeto (1sg=yo, 2sg=tú) y tiempo
VERB_CONJ: Dict[str, Dict[str, Dict[str, str]]] = {
    "ESTUDIAR": {"1sg": {"pres": "estudio", "fut": "estudiaré", "past": "estudié"},
                 "2sg": {"pres": "estudias", "fut": "estudiarás", "past": "estudiaste"}},
    "IR":       {"1sg": {"pres": "voy", "fut": "iré", "past": "fui"},
                 "2sg": {"pres": "vas", "fut": "irás", "past": "fuiste"}},
    "COMER":    {"1sg": {"pres": "como", "fut": "comeré", "past": "comí"},
                 "2sg": {"pres": "comes", "fut": "comerás", "past": "comiste"}},
    "BEBER":    {"1sg": {"pres": "bebo", "fut": "beberé", "past": "bebí"},
                 "2sg": {"pres": "bebes", "fut": "beberás", "past": "bebiste"}},
    "TRABAJAR": {"1sg": {"pres": "trabajo", "fut": "trabajaré", "past": "trabajé"},
                 "2sg": {"pres": "trabajas", "fut": "trabajarás", "past": "trabajaste"}},
    "AYUDAR":   {"1sg": {"pres": "ayudo", "fut": "ayudaré", "past": "ayudé"},
                 "2sg": {"pres": "ayudas", "fut": "ayudarás", "past": "ayudaste"}},
    "QUERER":   {"1sg": {"pres": "quiero", "fut": "querré", "past": "quise"},
                 "2sg": {"pres": "quieres", "fut": "querrás", "past": "quisiste"}},
}

# Lugar -> frase preposicional según la preposición que rige el verbo
PLACE = {
    "UNIVERSIDAD": {"en": "en la universidad", "a": "a la universidad"},
    "CASA": {"en": "en casa", "a": "a casa"},
    "TRABAJO": {"en": "en el trabajo", "a": "al trabajo"},
}

SUBJECT_PERSON = {"YO": "1sg", "TU": "2sg"}

# Glosas sueltas (cortesía / interjecciones)
STANDALONE = {
    "HOLA": "Hola", "GRACIAS": "Gracias", "POR_FAVOR": "Por favor",
    "SI": "Sí", "NO": "No", "BIEN": "Bien", "MAL": "Mal", "AYUDA": "Ayuda",
}


def _finish(text: str) -> str:
    text = text.strip()
    if not text:
        return text
    text = text[0].upper() + text[1:]
    if not text.endswith((".", "?", "!")):
        text += "."
    # Normaliza a NFC para una salida consistente (acentos/ñ)
    return unicodedata.normalize("NFC", text)


def compose(glosses: List[str], entities: Optional[Dict[str, str]] = None) -> Optional[str]:
    """Construye una oración a partir de glosas + entidades del contexto.

    Devuelve None si no puede componer (el llamador hará una unión simple).
    """
    entities = dict(entities or {})

    # Fusiona entidades acumuladas con las glosas actuales (estas mandan)
    slots = dict(entities)
    for g in glosses:
        cat = categorize(g)
        if cat:
            slots[cat] = g

    verb = slots.get("verb")
    place = slots.get("place")
    subject = slots.get("subject")
    time_marker = slots.get("time")

    # Caso con verbo: construye oración conjugada
    if verb and verb in VERB_CONJ:
        person = SUBJECT_PERSON.get(subject, "1sg")
        time_word, tense = TIME.get(time_marker, (None, "pres"))
        conj = VERB_CONJ[verb][person][tense]

        parts: List[str] = []
        if time_word:
            parts.append(time_word.lower())  # se capitaliza en _finish
        parts.append(conj)
        if place and place in PLACE:
            prep = "a" if verb == "IR" else "en"
            parts.append(PLACE[place][prep])
        return _finish(" ".join(parts))

    # Sin verbo: glosa(s) suelta(s) reconocidas
    words = [STANDALONE.get(g) for g in glosses if g in STANDALONE]
    if words:
        return _finish(", ".join(w.lower() for w in words))

    return None
