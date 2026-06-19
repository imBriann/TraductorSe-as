"""Agrega todas las rutas de la API v1."""
from fastapi import APIRouter

from app.api.routes import (
    dataset,
    health,
    realtime,
    settings as settings_routes,
    system,
    training,
    translations,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(system.router)
api_router.include_router(settings_routes.router)
api_router.include_router(translations.router)
api_router.include_router(realtime.router)
# Modo desarrollador (los propios endpoints validan DEV_MODE)
api_router.include_router(dataset.router)
api_router.include_router(training.router)
