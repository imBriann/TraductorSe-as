"""Consultas agregadas para estadísticas por dispositivo."""
from __future__ import annotations

from collections import Counter
from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.session import TranslationSession
from app.models.translation import Translation


async def device_summary(db: AsyncSession, device_id: int) -> dict:
    total_tr = await db.scalar(
        select(func.count(Translation.id)).where(Translation.device_id == device_id)
    )
    total_sessions = await db.scalar(
        select(func.count(TranslationSession.id)).where(
            TranslationSession.device_id == device_id
        )
    )
    avg_conf = await db.scalar(
        select(func.coalesce(func.avg(Translation.confidence), 0.0)).where(
            Translation.device_id == device_id
        )
    )
    avg_lat = await db.scalar(
        select(func.coalesce(func.avg(Translation.latency_ms), 0.0)).where(
            Translation.device_id == device_id
        )
    )

    rows: Sequence = (
        await db.execute(
            select(Translation.glosses).where(Translation.device_id == device_id)
        )
    ).scalars().all()
    counter: Counter = Counter()
    for glosses in rows:
        counter.update(glosses or [])
    top = [{"gloss": g, "count": c} for g, c in counter.most_common(10)]

    per_day_rows = await db.execute(
        select(
            func.date(Translation.created_at).label("day"),
            func.count(Translation.id).label("count"),
        )
        .where(Translation.device_id == device_id)
        .group_by(func.date(Translation.created_at))
        .order_by(func.date(Translation.created_at))
    )
    per_day = [{"day": str(r.day), "count": int(r.count)} for r in per_day_rows]

    return {
        "total_translations": int(total_tr or 0),
        "total_sessions": int(total_sessions or 0),
        "avg_confidence": round(float(avg_conf or 0.0), 4),
        "avg_latency_ms": round(float(avg_lat or 0.0), 2),
        "top_glosses": top,
        "translations_per_day": per_day,
    }
