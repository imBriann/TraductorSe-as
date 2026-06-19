"""Demostración end-to-end de la traducción CONTEXTUAL con los agentes i5.0.

Reproduce el caso objetivo del proyecto sin necesidad de cámara, Redis ni Ollama
(el Context Agent usa su almacén en memoria y el Agente Semántico su compositor
gramatical contextual). Con Ollama en marcha, el mismo flujo usa Llama 3.1.

Ejecutar:
    cd backend && python -m scripts.demo_context
"""
from __future__ import annotations

import asyncio
import sys
import unicodedata

# La consola de Windows (cp1252) no codifica acentos/emoji: forzamos UTF-8.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from app.agents.base import AgentContext
from app.agents.context import ContextAgent, _MEM
from app.agents.semantic import SemanticAgent
from app.services import ollama_service as ollama_mod


async def _turn(context: ContextAgent, semantic: SemanticAgent,
                session_key: str, glosses: list[str]) -> str:
    """Simula un turno: reconoce varias glosas y finaliza la frase."""
    ctx = AgentContext(session_key=session_key, context_enabled=True)
    for g in glosses:
        ctx.gloss = g
        ctx.accepted = True
        await context.load(ctx)
        await context.observe(ctx)
    ctx.generate_text = True
    await semantic.run(ctx)
    await context.write_back(ctx)
    return ctx.natural_text or ""


async def main() -> None:
    # Fuerza el modo offline (sin Ollama) para una demo instantánea y determinista
    async def _offline(*args, **kwargs):
        raise ConnectionError("Ollama no disponible (demo offline)")
    ollama_mod.ollama_service._generate = _offline  # type: ignore

    _MEM.clear()
    context = ContextAgent()
    semantic = SemanticAgent()
    sk = "demo-session"

    print("=" * 60)
    print(" DEMO — Traducción contextual con Agentes i5.0 (modo offline)")
    print("=" * 60)

    t1 = await _turn(context, semantic, sk, ["YO", "ESTUDIAR", "UNIVERSIDAD"])
    print(f"\nTurno 1  glosas: YO ESTUDIAR UNIVERSIDAD")
    print(f"         salida: {t1!r}")

    t2 = await _turn(context, semantic, sk, ["MAÑANA"])
    print(f"\nTurno 2  glosas: MAÑANA   (con contexto previo)")
    print(f"         salida: {t2!r}")

    print("\n" + "-" * 60)
    expected = "Mañana estudiaré en la universidad."
    ok = unicodedata.normalize("NFC", t2) == unicodedata.normalize("NFC", expected)
    print(f"Esperado turno 2: {expected!r}")
    print(f"Resultado       : {'[OK] CORRECTO' if ok else '[X] DIFERENTE'}")
    print("-" * 60)
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    asyncio.run(main())
