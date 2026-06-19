"""Configuración central de la aplicación basada en variables de entorno."""
from __future__ import annotations

from functools import lru_cache
from typing import List

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
    CONFIDENCE_THRESHOLD: float = 0.65

    # Dataset / entrenamiento (modo dev)
    DATA_DIR: str = "data"
    MODEL_STORE: str = "ml_store"

    @property
    def cors_origins(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
