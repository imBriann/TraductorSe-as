"""Verifica el Context Agent contra un Redis REAL (no el fallback en memoria).

Requiere REDIS_URL apuntando a un Redis accesible (p. ej. el contenedor `redis`
expuesto en localhost:6379). Ejecuta el flujo contextual de dos turnos y luego
inspecciona las claves del KV Cache en Redis.

Ejecutar (con db+redis arriba):
    set REDIS_URL=redis://localhost:6379/0
    cd backend && python -m scripts.verify_redis_context
"""
from __future__ import annotations

import asyncio
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from app.agents.base import AgentContext
from app.agents.context import ContextAgent
from app.agents.semantic import SemanticAgent
from app.core.redis_client import get_redis
from app.services import ollama_service as om


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


async def main() -> None:
    # Forzamos fallback gramatical (sin Ollama) para una verificación determinista
    async def _offline(*a, **k):
        raise ConnectionError("offline")
    om.ollama_service._generate = _offline  # type: ignore

    r = await get_redis()
    if r is None or not await r.ping():
        print("Redis NO disponible — exporta REDIS_URL a un Redis real.")
        raise SystemExit(2)
    print("Redis conectado:", await r.ping())

    context = ContextAgent()
    semantic = SemanticAgent()
    sk = "verify-redis-session"
    await context.reset(sk)

    t1 = await _turn(context, semantic, sk, ["YO", "ESTUDIAR", "UNIVERSIDAD"])
    print("Turno 1:", repr(t1.natural_text))
    t2 = await _turn(context, semantic, sk, ["MAÑANA"])
    print("Turno 2:", repr(t2.natural_text))

    # Inspecciona el KV Cache directamente en Redis
    print("\n-- Estado del KV Cache en Redis --")
    print("entities:", await r.hgetall(f"ctx:{sk}:entities"))
    print("history :", await r.lrange(f"ctx:{sk}:history", 0, -1))
    print("last_text:", await r.get(f"ctx:{sk}:last_text"))
    print("active  :", await r.smembers("ctx:active"))
    ttl = await r.ttl(f"ctx:{sk}:entities")
    print("TTL entities (s):", ttl)

    import unicodedata
    ok = unicodedata.normalize("NFC", t2.natural_text or "") == \
        unicodedata.normalize("NFC", "Mañana estudiaré en la universidad.")
    print("\nResultado:", "[OK] contexto en Redis + traducción correcta" if ok else "[X] diferente")
    await context.reset(sk)
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    asyncio.run(main())
