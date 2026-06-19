"""Punto de entrada de la aplicación FastAPI — LSC i5.0."""
from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app import __version__
from app.api.router import api_router
from app.core.config import settings
from app.core.database import init_models
from app.core.logging import configure_logging, logger
from app.core.redis_client import close_redis, get_redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    logger.info("Arrancando {} v{} ({})", settings.APP_NAME, __version__, settings.APP_ENV)
    await init_models()
    await get_redis()
    # Pre-carga del motor de inferencia
    from app.ml.inference import get_engine
    get_engine()
    yield
    await close_redis()
    logger.info("Apagando aplicación")


app = FastAPI(
    title="LSC i5.0 — API de Interpretación de Lengua de Señas Colombiana",
    description=(
        "API del Sistema Inteligente basado en Arquitectura de Agentes i5.0 "
        "(con Context Agent / KV Cache) y Llama 3.1 para la interpretación "
        "contextual de LSC. Acceso anónimo por dispositivo, sin autenticación."
    ),
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


# ---------------------------------------------------------------------------
# Servir el frontend desde el propio backend (modo local sin Nginx/Docker).
# En Docker el frontend lo sirve Nginx y este directorio no existe -> se omite.
# Debe montarse DESPUÉS de las rutas de la API para no eclipsarlas.
# ---------------------------------------------------------------------------
FRONTEND_DIR = os.environ.get("FRONTEND_DIR") or str(
    Path(__file__).resolve().parents[2] / "frontend"
)

if os.path.isdir(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
    logger.info("Sirviendo frontend estático desde {}", FRONTEND_DIR)
else:
    @app.get("/")
    async def root():
        return JSONResponse({
            "name": settings.APP_NAME,
            "version": __version__,
            "docs": "/docs",
            "api": settings.API_V1_PREFIX,
        })
