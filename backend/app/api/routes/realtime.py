"""WebSocket de traducción en tiempo real (contextual, basado en dispositivo).

Conexión: GET /api/v1/ws/translate?device=<uuid>&session_id=<opt>

Cliente → Servidor:
    { "type": "frame",    "landmarks": [..126 floats..] }
    { "type": "finalize" }     -> genera frase contextual + persiste
    { "type": "reset" }        -> limpia el contexto de la sesión

Servidor → Cliente:
    { "type": "ready",   "sequence_length": int }
    { "type": "partial", "gloss": str, "confidence": float, "buffer": [...], "entities": {...} }
    { "type": "final",   "text": str, "history": [...], "used_context": bool, "latency_ms": int }
    { "type": "error",   "detail": str }
"""
from __future__ import annotations

import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.agents.coordinator import CoordinatorAgent
from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.logging import logger
from app.crud import device as crud_device

router = APIRouter(tags=["realtime"])


@router.websocket("/ws/translate")
async def ws_translate(websocket: WebSocket, device: str | None = None,
                       session_id: int | None = None):
    await websocket.accept()

    async with AsyncSessionLocal() as db:
        dev = await crud_device.get_or_create(db, device)
        await db.commit()

        session_key = f"{dev.device_uid}:{session_id}" if session_id else dev.device_uid
        coordinator = CoordinatorAgent(db=db, threshold=dev.confidence_threshold)
        window: list[list[float]] = []
        seq_len = settings.SEQUENCE_LENGTH

        await websocket.send_json({"type": "ready", "sequence_length": seq_len})
        logger.info("WS abierto para device={}", dev.device_uid)

        try:
            while True:
                raw = await websocket.receive_text()
                try:
                    msg = json.loads(raw)
                except json.JSONDecodeError:
                    await websocket.send_json({"type": "error", "detail": "JSON inválido"})
                    continue

                mtype = msg.get("type")

                if mtype == "frame":
                    window.append(msg.get("landmarks", []))
                    if len(window) > seq_len:
                        window = window[-seq_len:]
                    ctx = await coordinator.process(
                        raw_sequence=window,
                        device_id=dev.id,
                        session_key=session_key,
                        session_id=session_id,
                        generate_text=False,
                        context_enabled=dev.context_enabled,
                        persist=False,
                        finalize=False,
                    )
                    await websocket.send_json({
                        "type": "partial",
                        "gloss": ctx.gloss,
                        "confidence": round(ctx.confidence, 4),
                        "buffer": ctx.glosses_buffer,
                        "entities": ctx.entities,
                    })

                elif mtype == "finalize":
                    ctx = await coordinator.process(
                        raw_sequence=window,
                        device_id=dev.id,
                        session_key=session_key,
                        session_id=session_id,
                        generate_text=True,
                        context_enabled=dev.context_enabled,
                        persist=True,
                        finalize=True,
                    )
                    await db.commit()
                    await websocket.send_json({
                        "type": "final",
                        "text": ctx.natural_text or "",
                        "history": ctx.history,
                        "used_context": ctx.used_context,
                        "latency_ms": ctx.latency_ms,
                    })
                    window = []

                elif mtype == "reset":
                    await coordinator.reset_context(session_key)
                    window = []
                    await websocket.send_json({"type": "reset_ok"})

                else:
                    await websocket.send_json({"type": "error", "detail": "Tipo desconocido"})

        except WebSocketDisconnect:
            logger.info("WS cerrado para device={}", dev.device_uid)
        except Exception as exc:  # pragma: no cover
            logger.exception("Error en WS: {}", exc)
            try:
                await websocket.send_json({"type": "error", "detail": str(exc)})
            except Exception:
                pass
