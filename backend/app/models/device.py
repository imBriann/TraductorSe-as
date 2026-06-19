"""Modelo de dispositivo anónimo.

Sustituye al modelo de usuario: no hay registro ni contraseñas. La identidad es
un UUID generado por el cliente (`device_uid`) que sirve únicamente para asociar
historial y preferencias. Es opcional desde el punto de vista del usuario.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    device_uid: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    label: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)  # alias opcional

    # Preferencias
    dark_mode: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    confidence_threshold: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    context_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    sessions: Mapped[list["TranslationSession"]] = relationship(  # noqa: F821
        back_populates="device", cascade="all, delete-orphan"
    )
    translations: Mapped[list["Translation"]] = relationship(  # noqa: F821
        back_populates="device", cascade="all, delete-orphan"
    )
