"""Configuración central de la aplicación basada en variables de entorno."""
from __future__ import annotations

from functools import lru_cache
from typing import List
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # General
    APP_NAME: str = "LSC i5.0"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    # Modo desarrollador (expone pantallas/endpoints de dataset y entrenamiento)
    DEV_MODE: bool = True

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://lsc:lsc_secret@db:5432/lsc_db"

    # Redis (backend del Context Agent / KV Cache)
    REDIS_URL: str = "redis://redis:6379/0"

    # Ollama
    OLLAMA_ENABLED: bool = True          # ponlo en false donde no haya Ollama (p. ej. Railway)
    OLLAMA_HOST: str = "http://ollama:11434"
    OLLAMA_MODEL: str = "llama3.1"
    OLLAMA_TIMEOUT: int = 60

    # Contexto conversacional (KV Cache)
    CONTEXT_TTL_SECONDS: int = 900       # persistencia temporal del contexto
    HISTORY_WINDOW: int = 5              # nº de frases previas conservadas
    MAX_CONTEXT_GLOSSES: int = 12        # nº máx. de glosas en el buffer activo

    # ML
    MODEL_PATH: str = "/app/ml_store/lsc_transformer.pt"
    LABELS_PATH: str = "/app/ml_store/labels.json"
    SEQUENCE_LENGTH: int = 30
    CONFIDENCE_THRESHOLD: float = 0.85   # solo se acepta una seña con prob > 85%

    # Filtros anti-spam de la inferencia en tiempo real
    DEBOUNCE_SECONDS: float = 1.5        # bloquea repetir la MISMA seña durante N s
    MOTION_DELTA_THRESHOLD: float = 0.008  # si la mano casi no se mueve, se ignora el frame

    # Dataset / entrenamiento (modo dev)
    DATA_DIR: str = "data"
    MODEL_STORE: str = "ml_store"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def _normalize_db_url(cls, v: str) -> str:
        """Compatibiliza la URL con el driver async asyncpg.

        Proveedores como Railway/Heroku entregan `postgres://` o `postgresql://`
        (driver síncrono) y a veces con `?sslmode=...`, que asyncpg no admite en
        la URL. Aquí se normaliza a `postgresql+asyncpg://` y se limpia la query.
        """
        if not isinstance(v, str) or not v:
            return v
        if v.startswith("postgres://"):
            v = "postgresql+asyncpg://" + v[len("postgres://"):]
        elif v.startswith("postgresql://"):
            v = "postgresql+asyncpg://" + v[len("postgresql://"):]

        if v.startswith("postgresql+asyncpg://") and "?" in v:
            parts = urlsplit(v)
            query = [(k, val) for k, val in parse_qsl(parts.query) if k.lower() != "sslmode"]
            v = urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))
        return v

    @property
    def cors_origins(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
