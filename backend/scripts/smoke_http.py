"""Smoke test HTTP: arranca la app en proceso (ASGI) y ejerce los endpoints.

Usa SQLite en memoria y NO requiere PostgreSQL/Redis/Ollama (degradación
elegante). Verifica health, system/info, settings e inferencia con dispositivo.

Ejecutar:  cd backend && python -m scripts.smoke_http
"""
from __future__ import annotations

import asyncio
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.main import app
from app.ml.constants import FEATURES_PER_FRAME

API = "/api/v1"


async def main() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    async def _get_db():
        async with Session() as s:
            yield s
            await s.commit()

    app.dependency_overrides[get_db] = _get_db
    transport = ASGITransport(app=app)
    failures = 0

    async with AsyncClient(transport=transport, base_url="http://test",
                           headers={"X-Device-Id": "smoke-001"}) as c:
        def check(name, cond):
            nonlocal failures
            print(f"  [{'OK ' if cond else 'XX '}] {name}")
            if not cond:
                failures += 1

        print("== Smoke test HTTP ==")
        r = await c.get(f"{API}/health")
        check("GET /health == 200", r.status_code == 200)

        r = await c.get(f"{API}/system/info")
        info = r.json()
        check("GET /system/info pipeline incluye 'Context'",
              r.status_code == 200 and "Context" in info.get("pipeline", []))
        print(f"        modelo_entrenado={info.get('model_trained')} clases={info.get('num_classes')}")

        await c.patch(f"{API}/settings/me", json={"confidence_threshold": 0.0})

        seq = [[0.2] * FEATURES_PER_FRAME for _ in range(30)]
        r = await c.post(f"{API}/translations/infer?finalize=true",
                         json={"sequence": seq, "generate_text": True})
        body = r.json()
        check("POST /translations/infer == 200", r.status_code == 200)
        check("infer devuelve glosa", bool(body.get("gloss")))
        check("infer devuelve texto natural", bool(body.get("natural_text")))
        print(f"        gloss={body.get('gloss')!r} texto={body.get('natural_text')!r} "
              f"latencia={body.get('latency_ms')}ms")

        r = await c.get(f"{API}/translations")
        check("GET /translations historial >= 1", len(r.json()) >= 1)

        r = await c.get(f"{API}/translations/export/pdf")
        check("GET /export/pdf == 200 (PDF)",
              r.status_code == 200 and r.content[:4] == b"%PDF")

        r = await c.get(f"{API}/dev/dataset")
        check("GET /dev/dataset == 200 (modo dev)", r.status_code == 200)

    app.dependency_overrides.clear()
    await engine.dispose()

    print("-" * 40)
    print(f"Resultado: {'TODO OK' if failures == 0 else f'{failures} FALLOS'}")
    raise SystemExit(0 if failures == 0 else 1)


if __name__ == "__main__":
    asyncio.run(main())
