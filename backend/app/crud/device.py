"""Operaciones CRUD para dispositivos anónimos."""
from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.device import Device


async def get_by_uid(db: AsyncSession, device_uid: str) -> Optional[Device]:
    res = await db.execute(select(Device).where(Device.device_uid == device_uid))
    return res.scalar_one_or_none()


async def get_or_create(db: AsyncSession, device_uid: Optional[str]) -> Device:
    """Obtiene el dispositivo por su UID o lo crea. Si no se provee UID, genera uno."""
    if device_uid:
        existing = await get_by_uid(db, device_uid)
        if existing:
            return existing
    device = Device(device_uid=device_uid or uuid.uuid4().hex)
    db.add(device)
    await db.flush()
    await db.refresh(device)
    return device


async def update(db: AsyncSession, device: Device, **fields) -> Device:
    for key, value in fields.items():
        if value is not None:
            setattr(device, key, value)
    await db.flush()
    await db.refresh(device)
    return device
