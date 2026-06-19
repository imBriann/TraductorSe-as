"""Entrenamiento del modelo (modo desarrollador).

Lanza el script de entrenamiento (`ml_training.train`) como un subproceso en
segundo plano y permite consultar su estado y la cola de salida (logs).
"""
from __future__ import annotations

import asyncio
import collections
from datetime import datetime, timezone
from typing import Deque, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.api.deps import require_dev_mode

router = APIRouter(prefix="/dev/training", tags=["dev"], dependencies=[Depends(require_dev_mode)])


class _TrainingState:
    """Estado global del job de entrenamiento (un job a la vez)."""

    def __init__(self) -> None:
        self.status: str = "idle"          # idle | running | finished | failed
        self.started_at: Optional[str] = None
        self.finished_at: Optional[str] = None
        self.return_code: Optional[int] = None
        self.logs: Deque[str] = collections.deque(maxlen=400)
        self.process: Optional[asyncio.subprocess.Process] = None


STATE = _TrainingState()


class TrainParams(BaseModel):
    epochs: int = 80
    batch_size: int = 32
    lr: float = 3e-4


class TrainingStatus(BaseModel):
    status: str
    started_at: Optional[str]
    finished_at: Optional[str]
    return_code: Optional[int]
    logs: list[str]


async def _stream_logs(proc: asyncio.subprocess.Process) -> None:
    assert proc.stdout is not None
    async for line in proc.stdout:
        STATE.logs.append(line.decode(errors="replace").rstrip())
    STATE.return_code = await proc.wait()
    STATE.status = "finished" if STATE.return_code == 0 else "failed"
    STATE.finished_at = datetime.now(timezone.utc).isoformat()


@router.post("/start", response_model=TrainingStatus, status_code=status.HTTP_202_ACCEPTED)
async def start_training(params: TrainParams):
    if STATE.status == "running":
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya hay un entrenamiento en curso")

    STATE.status = "running"
    STATE.started_at = datetime.now(timezone.utc).isoformat()
    STATE.finished_at = None
    STATE.return_code = None
    STATE.logs.clear()
    STATE.logs.append(
        f"Lanzando entrenamiento: epochs={params.epochs} "
        f"batch={params.batch_size} lr={params.lr}"
    )

    proc = await asyncio.create_subprocess_exec(
        "python", "-m", "ml_training.train",
        "--epochs", str(params.epochs),
        "--batch-size", str(params.batch_size),
        "--lr", str(params.lr),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    STATE.process = proc
    asyncio.create_task(_stream_logs(proc))

    return _current_status()


@router.get("/status", response_model=TrainingStatus)
async def training_status():
    return _current_status()


@router.post("/stop", response_model=TrainingStatus)
async def stop_training():
    if STATE.status == "running" and STATE.process is not None:
        try:
            STATE.process.terminate()
        except ProcessLookupError:
            pass
        STATE.status = "failed"
        STATE.logs.append("Entrenamiento detenido por el usuario.")
        STATE.finished_at = datetime.now(timezone.utc).isoformat()
    return _current_status()


def _current_status() -> TrainingStatus:
    return TrainingStatus(
        status=STATE.status,
        started_at=STATE.started_at,
        finished_at=STATE.finished_at,
        return_code=STATE.return_code,
        logs=list(STATE.logs),
    )
