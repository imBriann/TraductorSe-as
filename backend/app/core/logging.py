"""Configuración de logging con loguru."""
from __future__ import annotations

import sys

from loguru import logger

from app.core.config import settings


def configure_logging() -> None:
    logger.remove()
    level = "DEBUG" if settings.DEBUG else "INFO"
    logger.add(
        sys.stdout,
        level=level,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>"
        ),
        colorize=True,
    )
    logger.info("Logging configurado (nivel={})", level)


__all__ = ["logger", "configure_logging"]
