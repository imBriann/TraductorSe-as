# Despliegue en Railway

Railway despliega **un único servicio web** (el backend FastAPI, que también
sirve el frontend) + **PostgreSQL** y **Redis** gestionados. Railway da
**HTTPS automático** (`*.up.railway.app`), así que la cámara funciona sin
configurar certificados.

> **Sobre Llama 3 en Railway:** Railway **ofrece GPU**, así que puedes desplegar
> Ollama como un **segundo servicio** (con GPU + volumen) que descarga Llama 3
> automáticamente (ver §6). Mientras el modelo se descarga —o si prefieres no
> usar GPU— el sistema sigue funcionando con el *fallback* gramatical contextual.
>
> ⚠️ Railway **no usa `docker-compose`**: cada componente es un servicio. Los
> archivos `docker-compose*.yml` del repo son para un **servidor propio** (VPS),
> no para Railway. La GPU se activa en los **ajustes del servicio** de Railway.

Arquitectura en Railway:

```
Navegador ──HTTPS──▶  Servicio web (FastAPI + frontend)  ──▶  PostgreSQL (plugin)
                                  │                       └─▶  Redis (plugin)  → Context Agent / KV Cache
```

Archivos que usa Railway (ya incluidos en el repo):
- **`Dockerfile`** (raíz): empaqueta backend + frontend, escucha en `$PORT`.
- **`railway.json`**: builder Dockerfile + healthcheck `/api/v1/health`.

---

## 1. Subir el código a GitHub

Railway despliega desde un repositorio. Si aún no lo tienes en GitHub:

```bash
cd "TraductorSeñas"
git init && git add . && git commit -m "LSC i5.0"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/lsc-i5.git
git push -u origin main
```

---

## 2. Crear el proyecto en Railway

1. Entra a [railway.app](https://railway.app) → **New Project**.
2. **Deploy from GitHub repo** → elige tu repo. Railway detecta el `Dockerfile`
   y `railway.json` automáticamente y empieza a construir.

---

## 3. Añadir PostgreSQL y Redis

En el proyecto: **New → Database → Add PostgreSQL**. Repite con **Add Redis**.

---

## 4. Variables de entorno del servicio web

Abre el servicio web → pestaña **Variables** y añade (usa referencias a los
plugins para no copiar credenciales a mano):

| Variable | Valor |
|----------|-------|
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` |
| `REDIS_URL` | `${{Redis.REDIS_URL}}` |
| `OLLAMA_ENABLED` | `false` |
| `DEV_MODE` | `false` (o `true` si quieres las pantallas Dataset/Entrenamiento) |
| `APP_ENV` | `production` |
| `DEBUG` | `false` |

> No definas `PORT`: Railway lo inyecta y el contenedor ya lo respeta.
> El backend convierte solo la `DATABASE_URL` de Railway al driver async.

---

## 5. Generar el dominio y desplegar

1. Servicio web → **Settings → Networking → Generate Domain**.
   Obtendrás algo como `https://lsc-i5-production.up.railway.app`.
2. Railway redepliega al cambiar variables. Espera a que el build termine
   (la primera vez tarda unos minutos por las dependencias de Python).
3. Abre el dominio → **Empezar a traducir** → permite la cámara.

Comprobaciones:
```
https://TU-APP.up.railway.app/api/v1/health        -> {"status":"ok"}
https://TU-APP.up.railway.app/api/v1/system/info    -> estado (ollama_ok:false esperado)
```

---

## 6. Desplegar Ollama (Llama 3) en Railway con GPU — auto-descarga

El repo incluye un servicio Ollama listo en **`deploy/ollama/`** (Dockerfile +
`entrypoint.sh`) que **descarga el modelo solo** al arrancar.

1. En tu proyecto Railway: **New → GitHub Repo** (el mismo repo) para crear un
   **segundo servicio**. En sus **Settings**:
   - **Root Directory** = `deploy/ollama`  (usará ese Dockerfile).
   - **Enable GPU** (Railway lo expone en la configuración del servicio).
   - **Variables**: `OLLAMA_MODEL=llama3.1` (o `llama3`).
   - **Volumes**: añade un volumen montado en `/root/.ollama` para conservar el
     modelo entre despliegues (evita re-descargar los ~5 GB).
2. Espera a que arranque y descargue el modelo (mira los *Deploy Logs*:
   `descargando 'llama3.1'...`).
3. En el **servicio web** (el principal), añade/ajusta variables:
   - `OLLAMA_ENABLED=true`
   - `OLLAMA_HOST=http://<nombre-del-servicio-ollama>.railway.internal:11434`
   - `OLLAMA_MODEL=llama3.1`

El Agente Semántico usará ese Ollama; si falla o aún está descargando, recurre al
*fallback* (circuit breaker), así que nunca se queda sin responder.

> Nota de red: el servicio web alcanza a Ollama por la **red privada** de Railway
> (`*.railway.internal`). Si la conexión privada fallara por IPv6, define en el
> servicio Ollama `OLLAMA_BIND=[::]:11434` para que escuche también en IPv6.

---

## 7. Notas y límites

- **Memoria:** la imagen usa **torch en versión CPU** (más ligera). Aun así,
  elige un plan con suficiente RAM (≥ 1–2 GB). Si el build/arranque falla por
  memoria, sube el plan del servicio.
- **WebSocket:** funciona en Railway (el traductor en tiempo real va por `wss://`).
- **Reconocimiento real:** sin modelo entrenado se usa el *fallback* determinista.
  Para entrenar, pon `DEV_MODE=true`, usa la pantalla **Dataset** para grabar y
  **Entrenamiento** para lanzar el job. Para conservar el modelo entre despliegues
  añade un **Volume** de Railway montado en `/app/ml_store`.
- **Datos:** PostgreSQL y Redis son servicios gestionados de Railway (persisten).

---

## 8. Alternativa por CLI

```bash
npm i -g @railway/cli
railway login
railway init          # o: railway link  (a un proyecto existente)
railway up            # construye y despliega desde el Dockerfile
```

---

## 9. Solución de problemas

| Síntoma | Causa | Solución |
|---------|-------|----------|
| Build falla / OOM | Memoria insuficiente | Sube el plan; la imagen ya usa torch CPU |
| `connection refused` a la BD | Falta la referencia | `DATABASE_URL=${{Postgres.DATABASE_URL}}` |
| Healthcheck falla | App aún arrancando | El timeout es 300 s; revisa los *Deploy Logs* |
| Cámara no abre | (raro en Railway) | Asegúrate de usar la URL **https** del dominio |
| Texto muy básico | Sin LLM | Es el *fallback*; conecta un Ollama externo (§6) |
