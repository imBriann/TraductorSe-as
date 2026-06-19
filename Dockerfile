# ============================================================================
#  LSC i5.0 — Imagen única para Railway (u otro PaaS)
#  El backend FastAPI sirve TAMBIÉN el frontend estático, así que un solo
#  servicio web cubre API + WebSocket + UI. Escucha en el puerto $PORT que
#  inyecta la plataforma.
#
#  Servicios externos (conéctalos por variables de entorno en Railway):
#    - PostgreSQL  -> DATABASE_URL
#    - Redis       -> REDIS_URL
#    - (opcional) Ollama externo -> OLLAMA_HOST ; si no, OLLAMA_ENABLED=false
# ============================================================================
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    FRONTEND_DIR=/app/frontend

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential libgl1 libglib2.0-0 curl \
    && rm -rf /var/lib/apt/lists/*

# Dependencias (capa cacheable). torch en variante CPU (Railway no tiene GPU):
# imagen mucho más ligera y menor consumo de memoria.
COPY backend/requirements.txt .
RUN pip install --upgrade pip \
    && pip install torch==2.5.1 --index-url https://download.pytorch.org/whl/cpu \
    && pip install -r requirements.txt

# Código del backend y frontend
COPY backend/ /app/
COPY frontend/ /app/frontend/

RUN mkdir -p /app/ml_store

EXPOSE 8000

# Railway define $PORT; en local cae a 8000. --forwarded-allow-ips=* permite
# que detrás del proxy TLS de Railway el WebSocket funcione como wss://.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips=*"]
