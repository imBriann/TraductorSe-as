"""Métricas de uso agregadas (persistidas por el Agente de Persistencia)."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class UsageMetric(Base):
    __tablename__ = "usage_metrics"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    device_id: Mapped[int] = mapped_column(
        ForeignKey("devices.id", ondelete="CASCADE"), index=True
    )

    event: Mapped[str] = mapped_column(String(80), index=True)  # ej: "translation"
    value: Mapped[float] = mapped_column(Float, default=1.0)
    avg_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    avg_latency_ms: Mapped[float] = mapped_column(Float, default=0.0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
