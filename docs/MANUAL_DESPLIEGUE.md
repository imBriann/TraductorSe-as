# Manual de Despliegue — LSC i5.0

Este manual describe el despliegue completo del sistema, tanto con Docker
(recomendado) como en modo desarrollo local.

---

## 1. Requisitos

| Componente | Versión mínima | Notas |
|-----------|----------------|-------|
| Docker | 24+ | Con Docker Compose v2 |
| RAM | 8 GB | Llama 3.1 8B requiere memoria |
| Disco | 15 GB | Imágenes + modelo Ollama |
| Navegador | Chrome/Edge/Firefox recientes | Requiere WebRTC y `getUserMedia` |
| (Local) Python | 3.11+ | Solo para desarrollo sin Docker |

> **Cámara y HTTPS:** los navegadores solo permiten acceso a la cámara en
> `localhost` o sobre HTTPS. En producción, sirve el frontend tras un proxy
> TLS (Nginx/Traefik/Caddy).

---

## 2. Despliegue con Docker Compose (recomendado)

```bash
cd TraductorSeñas
cp .env.example .env
```

Edita `.env` y ajusta según necesites:

- `POSTGRES_PASSWORD` → contraseña robusta.
- `DEV_MODE` → `true` para exponer las pantallas de Dataset y Entrenamiento; `false` para ocultarlas.
- `CONTEXT_TTL_SECONDS` → tiempo de vida del contexto conversacional (KV Cache).

> No hay autenticación ni usuario administrador: la plataforma es de acceso
> anónimo inmediato (identidad por dispositivo).

Levanta el stack:

```bash
docker compose up -d --build
```

Servicios y puertos por defecto:

| Servicio | URL / Puerto |
|----------|--------------|
| Frontend (Nginx) | http://localhost:3000 |
| Backend (FastAPI) | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| PostgreSQL | localhost:5432 |
| Redis | localhost:6379 |
| Ollama | localhost:11434 |

### Descarga del modelo Llama 3.1

El contenedor `ollama` ejecuta `scripts/ollama-entrypoint.sh`, que descarga
automáticamente el modelo definido en `OLLAMA_MODEL` (por defecto `llama3.1`)
la primera vez. Sigue el progreso con:

```bash
docker compose logs -f ollama
```

Hasta que termine la descarga, el Agente Semántico usa el *fallback* local.

### Comandos útiles

```bash
docker compose ps                 # estado
docker compose logs -f backend    # logs del backend
docker compose restart backend    # reiniciar un servicio
docker compose down               # detener (conserva volúmenes)
docker compose down -v            # detener y borrar datos
```

### Verificación

```bash
curl http://localhost:8000/api/v1/health
curl http://localhost:8000/api/v1/health/full   # estado de redis/ollama/modelo
```

---

## 3. Desarrollo local (sin Docker)

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Requiere PostgreSQL accesible; ajusta variables:
export DATABASE_URL="postgresql+asyncpg://lsc:lsc_secret@localhost:5432/lsc_db"
export REDIS_URL="redis://localhost:6379/0"
export OLLAMA_HOST="http://localhost:11434"

uvicorn app.main:app --reload --port 8000
```

> Sin Redis/Ollama el backend degrada con elegancia: el Context Agent usa un
> almacén en memoria y el Agente Semántico un *fallback* gramatical local.
> **PostgreSQL es obligatorio** para el historial.

### Frontend (modo local)

En desarrollo local **el propio backend sirve el frontend**: cuando existe el
directorio `frontend/`, FastAPI lo monta en `/`. No necesitas un segundo
servidor ni configurar proxy.

```
uvicorn app.main:app --reload --port 8000   # sirve API + frontend
# Abre:  http://localhost:8000
```

Así la app y la API comparten origen (`http://localhost:8000`), por lo que el
WebSocket `/api/v1/ws/translate` y las rutas `/api/v1/...` funcionan sin proxy
ni CORS.

> **No uses** `python -m http.server` para el frontend en local: ese servidor
> estático **no redirige** `/api` al backend y la traducción no funcionará
> (verás 404 en `/api/v1/system/info` y en el WebSocket).
>
> Puedes ubicar el frontend en otra ruta con la variable `FRONTEND_DIR`. En
> Docker, Nginx sirve el frontend y este montaje se omite automáticamente.

---

## 4. Despliegue en producción

1. Coloca un proxy inverso con **TLS** delante del frontend.
2. Define `APP_ENV=production` y `DEBUG=false`.
3. Define `DEV_MODE=false` para ocultar las pantallas/endpoints de dataset y entrenamiento.
4. Restringe `ALLOWED_ORIGINS` a tu dominio real.
5. El backend es *stateless*: el contexto vive en Redis (KV Cache), por lo que
   escala horizontalmente con varias réplicas.
6. Habilita backups de PostgreSQL (`pgdata`).

---

## 5. Solución de problemas

| Síntoma | Causa probable | Solución |
|---------|----------------|----------|
| `backend` reinicia en bucle | DB no lista | Espera al healthcheck de `db`; revisa `DATABASE_URL` |
| Texto no natural | Ollama aún descargando | Espera; mira `docker compose logs ollama` |
| Cámara no abre | Sin HTTPS / permisos | Usa `localhost` o TLS; concede permisos |
| No se traduce con contexto | Redis no disponible | Revisa el servicio `redis`; sin él se usa memoria local (sin TTL) |
| Pantallas Dataset/Entrenamiento ausentes | `DEV_MODE=false` | Ponlo en `true` y reinicia el backend |
| WebSocket no conecta | Proxy WS mal configurado | Revisa `location /api/v1/ws/` en `nginx.conf` |
