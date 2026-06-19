"""Modelo de sesión de traducción (una conversación contextual)."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class TranslationSession(Base):
    __tablename__ = "translation_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    device_id: Mapped[int] = mapped_column(
        ForeignKey("devices.id", ondelete="CASCADE"), index=True
    )

    title: Mapped[str] = mapped_column(String(255), default="Conversación")
    total_signs: Mapped[int] = mapped_column(Integer, default=0)

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    device: Mapped["Device"] = relationship(back_populates="sessions")  # noqa: F821
    translations: Mapped[list["Translation"]] = relationship(  # noqa: F821
        back_populates="session", cascade="all, delete-orphan"
    )
