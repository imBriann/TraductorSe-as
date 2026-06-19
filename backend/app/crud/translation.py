"""CRUD para sesiones y traducciones (basado en dispositivo)."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.session import TranslationSession
from app.models.translation import Translation
from app.schemas.translation import TranslationCreate


# ---------------------------------------------------------------- Sesiones
async def create_session(
    db: AsyncSession, device_id: int, title: str = "Conversación"
) -> TranslationSession:
    session = TranslationSession(device_id=device_id, title=title)
    db.add(session)
    await db.flush()
    await db.refresh(session)
    return session


async def end_session(db: AsyncSession, session: TranslationSession) -> TranslationSession:
    session.ended_at = datetime.now(timezone.utc)
    await db.flush()
    return session


async def get_session(db: AsyncSession, session_id: int) -> Optional[TranslationSession]:
    return await db.get(TranslationSession, session_id)


async def list_sessions(
    db: AsyncSession, device_id: int, skip: int = 0, limit: int = 50
) -> Sequence[TranslationSession]:
    res = await db.execute(
        select(TranslationSession)
        .where(TranslationSession.device_id == device_id)
        .order_by(TranslationSession.started_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return res.scalars().all()


# ------------------------------------------------------------ Traducciones
async def create_translation(
    db: AsyncSession, device_id: int, data: TranslationCreate
) -> Translation:
    tr = Translation(
        device_id=device_id,
        session_id=data.session_id,
        glosses=data.glosses,
        natural_text=data.natural_text,
        confidence=data.confidence,
        latency_ms=data.latency_ms,
        source=data.source,
        used_context=data.used_context,
    )
    db.add(tr)
    if data.session_id:
        session = await db.get(TranslationSession, data.session_id)
        if session:
            session.total_signs += len(data.glosses)
    await db.flush()
    await db.refresh(tr)
    return tr


async def list_translations(
    db: AsyncSession, device_id: int, skip: int = 0, limit: int = 50,
    session_id: Optional[int] = None,
) -> Sequence[Translation]:
    stmt = select(Translation).where(Translation.device_id == device_id)
    if session_id is not None:
        stmt = stmt.where(Translation.session_id == session_id)
    stmt = stmt.order_by(Translation.created_at.desc()).offset(skip).limit(limit)
    res = await db.execute(stmt)
    return res.scalars().all()


async def get_translation(db: AsyncSession, tr_id: int) -> Optional[Translation]:
    return await db.get(Translation, tr_id)


async def delete_translation(db: AsyncSession, tr: Translation) -> None:
    await db.delete(tr)
    await db.flush()
