"""Rutas de preferencias del dispositivo y estadísticas propias."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_device
from app.core.database import get_db
from app.crud import device as crud_device
from app.crud import stats as crud_stats
from app.models.device import Device
from app.schemas.settings import DeviceOut, DeviceSettingsUpdate
from app.schemas.stats import StatsSummary

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/me", response_model=DeviceOut)
async def read_settings(device: Device = Depends(get_device)):
    return device


@router.patch("/me", response_model=DeviceOut)
async def update_settings(
    data: DeviceSettingsUpdate,
    device: Device = Depends(get_device),
    db: AsyncSession = Depends(get_db),
):
    return await crud_device.update(
        db, device,
        label=data.label,
        dark_mode=data.dark_mode,
        confidence_threshold=data.confidence_threshold,
        context_enabled=data.context_enabled,
    )


@router.get("/stats", response_model=StatsSummary)
async def my_stats(
    device: Device = Depends(get_device),
    db: AsyncSession = Depends(get_db),
):
    return await crud_stats.device_summary(db, device.id)
