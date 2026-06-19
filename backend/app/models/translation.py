"""Modelo de traducción individual (resultado del pipeline de agentes)."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Translation(Base):
    __tablename__ = "translations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    device_id: Mapped[int] = mapped_column(
        ForeignKey("devices.id", ondelete="CASCADE"), index=True
    )
    session_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("translation_sessions.id", ondelete="CASCADE"), nullable=True, index=True
    )

    # Glosas reconocidas, ej: ["YO","ESTUDIAR","UNIVERSIDAD","MAÑANA"]
    glosses: Mapped[list] = mapped_column(JSON, default=list)
    # Texto natural generado por Llama 3.1 (con contexto)
    natural_text: Mapped[str] = mapped_column(Text, default="")
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    source: Mapped[str] = mapped_column(String(40), default="realtime")
    used_context: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    device: Mapped["Device"] = relationship(back_populates="translations")  # noqa: F821
    session: Mapped[Optional["TranslationSession"]] = relationship(  # noqa: F821
        back_populates="translations"
    )
