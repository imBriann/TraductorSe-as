"""Gestión de dataset (modo desarrollador).

Permite inspeccionar las clases del dataset y grabar nuevas muestras de
secuencias de landmarks capturadas desde el navegador.
"""
from __future__ import annotations

import os
from typing import List

import numpy as np
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.api.deps import require_dev_mode
from app.core.config import settings
from app.ml.constants import FEATURES_PER_FRAME

router = APIRouter(prefix="/dev/dataset", tags=["dev"], dependencies=[Depends(require_dev_mode)])


def _seq_dir() -> str:
    return os.path.join(settings.DATA_DIR, "sequences")


class ClassInfo(BaseModel):
    label: str
    samples: int


class DatasetSummary(BaseModel):
    classes: List[ClassInfo]
    total_samples: int
    total_classes: int


class SampleIn(BaseModel):
    label: str = Field(min_length=1, max_length=64)
    sequence: List[List[float]]


@router.get("", response_model=DatasetSummary)
async def dataset_summary():
    base = _seq_dir()
    classes: List[ClassInfo] = []
    total = 0
    if os.path.isdir(base):
        for label in sorted(os.listdir(base)):
            cdir = os.path.join(base, label)
            if os.path.isdir(cdir):
                n = len([f for f in os.listdir(cdir) if f.endswith(".npy")])
                classes.append(ClassInfo(label=label, samples=n))
                total += n
    return DatasetSummary(classes=classes, total_samples=total, total_classes=len(classes))


@router.post("/sample", status_code=status.HTTP_201_CREATED)
async def add_sample(sample: SampleIn):
    if not sample.sequence:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Secuencia vacía")

    arr = np.asarray(sample.sequence, dtype=np.float32)
    if arr.ndim != 2 or arr.shape[1] != FEATURES_PER_FRAME:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Cada frame debe tener {FEATURES_PER_FRAME} valores",
        )

    label = sample.label.upper().replace(" ", "_")
    out_dir = os.path.join(_seq_dir(), label)
    os.makedirs(out_dir, exist_ok=True)
    idx = len([f for f in os.listdir(out_dir) if f.endswith(".npy")]) + 1
    path = os.path.join(out_dir, f"{label}_{idx:04d}.npy")
    np.save(path, arr)
    return {"saved": path, "label": label, "frames": int(arr.shape[0])}
