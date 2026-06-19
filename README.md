# 🇨🇴 LSC i5.0 — Sistema Inteligente de Interpretación de Lengua de Señas Colombiana

Plataforma **full-stack de acceso inmediato** que interpreta **Lengua de Señas
Colombiana (LSC)** en tiempo real desde el navegador, combinando **visión
computacional (MediaPipe)**, un **Transformer temporal** para clasificación de
señas, un **Context Agent con memoria contextual (KV Cache en Redis)** y
**Llama 3.1** (vía Ollama) para generar texto natural en español **considerando
el contexto previo** — todo orquestado mediante una **arquitectura de agentes i5.0**.

> **Sin registro ni login.** La plataforma se usa de inmediato; la identidad es un
> UUID anónimo por dispositivo, solo para guardar historial y preferencias.

```
Camera → MediaPipe → Perception → Preprocessing → Recognition → Context → Semantic (Llama 3.1) → Persistence → Frontend
```

> **Traducción contextual:** `YO ESTUDIAR UNIVERSIDAD` y luego `MAÑANA`
> → *"Mañana estudiaré en la universidad."*

---

## ✨ Características

- 🎥 **Traducción en tiempo real** vía WebRTC + WebSocket, con **auto-traducción al pausar** (mínimos clics).
- 🧠 **Transformer temporal** (PyTorch) sobre landmarks 3D de ambas manos.
- 🗃️ **Context Agent + KV Cache (Redis)**: recuerda señas, entidades y frases previas; persistencia temporal configurable.
- 💬 **Generación de lenguaje natural contextual** con Llama 3.1 (reutiliza el `context` KV del modelo); *fallback* gramatical local.
- 🔓 **Acceso anónimo por dispositivo** — sin cuentas, sin contraseñas, sin roles.
- 🕑 **Historial** y **exportación** a PDF, DOCX y TXT.
- ⚙️ **Configuración**: tema, memoria contextual, umbral de confianza.
- ℹ️ **Información del sistema**: estado de Redis/Ollama/modelo y diagrama del pipeline.
- 🧰 **Modo desarrollador**: gestión de **dataset** (grabación de muestras desde el navegador) y **entrenamiento** del modelo.
- 🌓 **Modo oscuro**, diseño **responsive** (mobile-first) y **accesible**.
- 🐳 **Docker Compose** (PostgreSQL + Redis + Ollama + Backend + Frontend) y 🧪 **tests** (pytest).

---

## 🏗️ Arquitectura de Agentes i5.0

```
┌──────────────┐      WS / HTTP        ┌──────────────────────────────────────────┐
│   Frontend   │ ───────────────────▶  │              Backend (FastAPI)             │
│ HTML/JS/Tail │   landmarks 3D        │   ┌──────────── Coordinador ───────────┐  │
│ MediaPipe JS │   (X-Device-Id)       │   │ Percepción                          │  │
│   WebRTC     │ ───────────────────▶  │   │  → Preprocesamiento (EWMA)          │  │
└──────────────┘                       │   │  → Reconocimiento (Transformer)     │  │
                                       │   │  → Context Agent ⇄ Redis (KV Cache) │  │
                                       │   │  → Semántico  → Ollama / Llama 3.1  │  │
                                       │   │  → Persistencia                     │  │
                                       │   └─────────────────────────────────────┘  │
                                       └──────┬──────────────┬───────────┬──────────┘
                                          ┌───▼────┐   ┌─────▼────┐  ┌───▼────┐
                                          │Postgres│   │  Redis   │  │ Ollama │
                                          └────────┘   │ KV Cache │  └────────┘
                                                       └──────────┘
```

El **Context Agent** recupera la memoria conversacional **antes** de cada
inferencia y la actualiza **después**, habilitando traducciones contextuales.
Detalle en [`docs/MANUAL_TECNICO.md`](docs/MANUAL_TECNICO.md).

---

## 📁 Estructura del proyecto

```
TraductorSeñas/
├── docker-compose.yml          # Orquestación completa
├── .env.example                # Variables de entorno
├── scripts/ollama-entrypoint.sh
├── backend/
│   ├── Dockerfile  requirements.txt  pytest.ini
│   ├── db/init/                # SQL de inicialización
│   ├── app/
│   │   ├── main.py             # FastAPI + lifespan (sin bootstrap de admin)
│   │   ├── core/               # config, db, redis, logging
│   │   ├── models/             # device, session, translation, metric
│   │   ├── schemas/            # settings, translation, stats
│   │   ├── crud/               # device, translation, stats
│   │   ├── agents/             # Agentes i5.0 (incluye context.py ⭐)
│   │   ├── ml/                 # Transformer, inferencia, labels (+ entidades)
│   │   ├── services/           # Ollama (contextual), exportación
│   │   └── api/                # health, system, settings, translations,
│   │       └── routes/         #   realtime (WS), dev/dataset, dev/training
│   ├── ml_training/            # capture, label, augment, dataset, train, validate
│   └── tests/                  # pytest (unit + integración + Context Agent)
├── frontend/
│   ├── Dockerfile  nginx.conf
│   ├── index.html (Inicio)  translator.html  history.html
│   ├── configuracion.html  info.html
│   ├── dataset.html  training.html      # modo desarrollador
│   ├── css/styles.css
│   └── js/ (config, api, ui, translator)
└── docs/  (MANUAL_DESPLIEGUE · MANUAL_TECNICO · MANUAL_USUARIO)
```

---

## 🚀 Instalación rápida (Docker)

```bash
cd TraductorSeñas
cp .env.example .env          # ajusta credenciales de PostgreSQL si quieres
docker compose up -d --build

# Frontend:  http://localhost:3000   (¡listo para usar, sin login!)
# API docs:  http://localhost:8000/docs
```

El contenedor de Ollama descarga `llama3.1` automáticamente la primera vez
(sigue el progreso con `docker compose logs -f ollama`). Hasta entonces, el
Agente Semántico usa el *fallback* local. Detalle en
[`docs/MANUAL_DESPLIEGUE.md`](docs/MANUAL_DESPLIEGUE.md).

### 🌐 Desplegar en un servidor (dominio + HTTPS + GPU)

Para alojarlo en un equipo más potente accesible desde internet con HTTPS
automático (Caddy + Let's Encrypt) y, opcionalmente, GPU NVIDIA:

```bash
cp .env.example .env          # define DOMAIN=tu-dominio.com
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
# con GPU:  añade  -f docker-compose.gpu.yml
```

Guía paso a paso (Ubuntu): **[`docs/DESPLIEGUE_SERVIDOR.md`](docs/DESPLIEGUE_SERVIDOR.md)**.

---

## 🖥️ Pantallas

| Pantalla | Descripción |
|----------|-------------|
| **Inicio** | Acceso inmediato; un clic abre el traductor y la cámara |
| **Traductor** | Tiempo real, contextual, con auto-traducción al pausar |
| **Historial** | Traducciones del dispositivo + exportación PDF/DOCX/TXT |
| **Configuración** | Tema, memoria contextual, umbral, estadísticas |
| **Información** | Estado del sistema y diagrama del pipeline |
| **Dataset** *(dev)* | Grabar muestras de señas desde el navegador |
| **Entrenamiento** *(dev)* | Lanzar y monitorizar el entrenamiento del modelo |

Las pantallas *dev* se muestran solo si `DEV_MODE=true`.

---

## 🧠 Entrenar el modelo

Sin modelo entrenado, el backend opera en modo *fallback* determinista. Para
entrenar (CLI o desde la pantalla **Entrenamiento**):

```bash
cd backend && pip install -r requirements.txt
python -m ml_training.capture  --label HOLA --samples 40
python -m ml_training.label    --review data/sequences
python -m ml_training.augment  --factor 4
python -m ml_training.train    --epochs 80
python -m ml_training.validate
```

El checkpoint `ml_store/lsc_transformer.pt` se carga automáticamente.

---

## 🧪 Tests y verificación

```bash
cd backend && pip install -r requirements.txt
pytest                              # 29 tests (unit + integración + contexto)

# Demo de traducción CONTEXTUAL end-to-end (sin cámara/Redis/Ollama):
python -m scripts.demo_context      # YO ESTUDIAR UNIVERSIDAD → ... → MAÑANA
#   Turno 1: "Estudio en la universidad."
#   Turno 2: "Mañana estudiaré en la universidad."   ← usa el contexto previo

# Smoke test HTTP de la API (SQLite en memoria, sin dependencias externas):
python -m scripts.smoke_http        # health, system/info, infer, export, dev

# Verificación del KV Cache contra Redis REAL (requiere Redis en marcha):
#   docker compose up -d redis
#   $env:REDIS_URL="redis://localhost:6379/0"; python -m scripts.verify_redis_context
```

---

## 📡 API (resumen)

Documentación interactiva: **http://localhost:8000/docs**. Todas las rutas usan
la cabecera `X-Device-Id` (identidad anónima); no hay autenticación.

| Método | Ruta | Descripción |
|-------|------|-------------|
| GET | `/api/v1/system/info` | Estado del sistema y pipeline |
| GET/PATCH | `/api/v1/settings/me` | Preferencias del dispositivo |
| GET | `/api/v1/settings/stats` | Estadísticas del dispositivo |
| POST | `/api/v1/translations/infer` | Inferencia contextual (REST) |
| POST | `/api/v1/translations/context/reset` | Limpiar contexto |
| GET/DELETE | `/api/v1/translations` | Historial |
| GET | `/api/v1/translations/export/{pdf\|docx\|txt}` | Exportar |
| WS | `/api/v1/ws/translate?device=<uuid>` | Traducción en tiempo real |
| GET/POST | `/api/v1/dev/dataset` · `/dev/dataset/sample` | Dataset (dev) |
| POST/GET | `/api/v1/dev/training/start` · `/status` · `/stop` | Entrenamiento (dev) |

---

## 📜 Licencia

Proyecto académico — 8º Semestre, Modelado y Simulación de Sistemas Continuos.
Uso educativo y de investigación.
