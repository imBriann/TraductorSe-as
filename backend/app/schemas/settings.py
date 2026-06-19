from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class DeviceSettingsUpdate(BaseModel):
    label: Optional[str] = Field(default=None, max_length=120)
    dark_mode: Optional[bool] = None
    confidence_threshold: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    context_enabled: Optional[bool] = None


class DeviceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    device_uid: str
    label: Optional[str]
    dark_mode: bool
    confidence_threshold: Optional[float]
    context_enabled: bool
    created_at: datetime
