"""Rutas de traducción: inferencia REST, sesiones, historial, export, contexto."""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.coordinator import CoordinatorAgent
from app.api.deps import get_device
from app.core.database import get_db
from app.crud import translation as crud_tr
from app.models.device import Device
from app.schemas.translation import (
    InferenceRequest,
    InferenceResult,
    SessionOut,
    TranslationOut,
)
from app.services.export_service import EXPORTERS

router = APIRouter(prefix="/translations", tags=["translations"])


def _session_key(device: Device, session_id: Optional[int]) -> str:
    return f"{device.device_uid}:{session_id}" if session_id else device.device_uid


# ----------------------------------------------------------- inferencia
@router.post("/infer", response_model=InferenceResult)
async def infer(
    req: InferenceRequest,
    finalize: bool = Query(default=True, description="Genera texto y persiste"),
    device: Device = Depends(get_device),
    db: AsyncSession = Depends(get_db),
):
    threshold = device.confidence_threshold
    coordinator = CoordinatorAgent(db=db, threshold=threshold)
    ctx = await coordinator.process(
        raw_sequence=req.sequence,
        device_id=device.id,
        session_key=_session_key(device, req.session_id),
        session_id=req.session_id,
        generate_text=req.generate_text,
        context_enabled=device.context_enabled,
        persist=True,
        finalize=finalize,
    )
    return InferenceResult(
        gloss=ctx.gloss or "DESCONOCIDO",
        confidence=ctx.confidence,
        glosses_buffer=ctx.glosses_buffer,
        natural_text=ctx.natural_text,
        entities=ctx.entities,
        history=ctx.history,
        used_context=ctx.used_context,
        latency_ms=ctx.latency_ms,
    )


@router.post("/context/reset", status_code=status.HTTP_204_NO_CONTENT)
async def reset_context(
    session_id: Optional[int] = None,
    device: Device = Depends(get_device),
):
    coordinator = CoordinatorAgent(db=None)
    await coordinator.reset_context(_session_key(device, session_id))


# ------------------------------------------------------------- sesiones
@router.post("/sessions", response_model=SessionOut, status_code=201)
async def create_session(
    title: str = "Conversación",
    device: Device = Depends(get_device),
    db: AsyncSession = Depends(get_db),
):
    return await crud_tr.create_session(db, device.id, title=title)


@router.get("/sessions", response_model=List[SessionOut])
async def list_sessions(
    skip: int = 0, limit: int = Query(50, le=200),
    device: Device = Depends(get_device),
    db: AsyncSession = Depends(get_db),
):
    return await crud_tr.list_sessions(db, device.id, skip, limit)


@router.post("/sessions/{session_id}/end", response_model=SessionOut)
async def end_session(
    session_id: int,
    device: Device = Depends(get_device),
    db: AsyncSession = Depends(get_db),
):
    s = await crud_tr.get_session(db, session_id)
    if not s or s.device_id != device.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sesión no encontrada")
    return await crud_tr.end_session(db, s)


# ------------------------------------------------------------ historial
@router.get("", response_model=List[TranslationOut])
async def history(
    skip: int = 0,
    limit: int = Query(50, le=200),
    session_id: Optional[int] = None,
    device: Device = Depends(get_device),
    db: AsyncSession = Depends(get_db),
):
    return await crud_tr.list_translations(db, device.id, skip, limit, session_id)


@router.delete("/{tr_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_translation(
    tr_id: int,
    device: Device = Depends(get_device),
    db: AsyncSession = Depends(get_db),
):
    tr = await crud_tr.get_translation(db, tr_id)
    if not tr or tr.device_id != device.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Traducción no encontrada")
    await crud_tr.delete_translation(db, tr)


# -------------------------------------------------------------- export
@router.get("/export/{fmt}")
async def export(
    fmt: str,
    limit: int = Query(500, le=2000),
    device: Device = Depends(get_device),
    db: AsyncSession = Depends(get_db),
):
    if fmt not in EXPORTERS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Formato no soportado (txt|docx|pdf)")
    exporter, mime, ext = EXPORTERS[fmt]
    items = await crud_tr.list_translations(db, device.id, 0, limit)
    items = list(reversed(items))  # orden cronológico ascendente
    content = exporter(items)
    headers = {"Content-Disposition": f'attachment; filename="traducciones_lsc.{ext}"'}
    return StreamingResponse(iter([content]), media_type=mime, headers=headers)
