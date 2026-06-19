"""Dependencias compartidas de la API.

Identidad anónima: el cliente envía su UUID en la cabecera `X-Device-Id`. Si no
existe el dispositivo se crea automáticamente. No hay autenticación.
"""
from __future__ import annotations

from typing import Optional

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.crud import device as crud_device
from app.models.device import Device


async def get_device(
    x_device_id: Optional[str] = Header(default=None, alias="X-Device-Id"),
    db: AsyncSession = Depends(get_db),
) -> Device:
    """Resuelve (o crea) el dispositivo anónimo a partir de la cabecera."""
    return await crud_device.get_or_create(db, x_device_id)


async def require_dev_mode() -> None:
    """Bloquea los endpoints de desarrollador si DEV_MODE está desactivado."""
    if not settings.DEV_MODE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Modo desarrollador desactivado (DEV_MODE=false)",
        )
