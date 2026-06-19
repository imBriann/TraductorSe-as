# Manual Técnico — LSC i5.0

Referencia técnica para desarrolladores que mantengan o extiendan el sistema.

---

## 1. Visión general

El sistema interpreta Lengua de Señas Colombiana con una **arquitectura de
agentes i5.0**. La captura de vídeo y la extracción de landmarks ocurren en el
**cliente** (MediaPipe Hands); el **backend** ejecuta preprocesamiento,
clasificación, **gestión de contexto**, generación semántica y persistencia.

**No hay autenticación.** La identidad es un UUID anónimo por dispositivo
(`X-Device-Id` en REST, `?device=` en el WebSocket), usado solo para historial y
preferencias.

### Pipeline

```
Camera → MediaPipe → Perception → Preprocessing → Recognition → Context → Semantic(Llama 3.1) → Persistence → Frontend
```

```
Navegador                          Backend (Coordinador)
getUserMedia → MediaPipe Hands
   │ 126 floats/frame (WS)
   ▼
PerceptionAgent        (validación)
PreprocessingAgent     (normalización + EWMA)
RecognitionAgent       (Transformer → glosa + confianza, accepted?)
ContextAgent.load      (recupera memoria de Redis: glosas/entidades/historial/KV)
ContextAgent.observe   (registra la seña aceptada; clasifica entidad)
   │ (al finalizar la frase)
SemanticAgent          (Llama 3.1 con contexto + KV cache) 
ContextAgent.write_back (guarda frase en historial, cierra buffer)
PersistenceAgent       (PostgreSQL + métricas Redis)
```

---

## 2. Arquitectura de Agentes i5.0

| Agente | Archivo | Responsabilidad |
|--------|---------|-----------------|
| **Percepción** | `agents/perception.py` | Valida/estructura landmarks |
| **Preprocesamiento** | `agents/preprocessing.py` | Normaliza, filtra ruido, **EWMA** |
| **Reconocimiento** | `agents/recognition.py` | Transformer; marca `accepted` según umbral |
| **Contexto** ⭐ | `agents/context.py` | Memoria conversacional (KV Cache Redis) |
| **Semántico** | `agents/semantic.py` | Llama 3.1 con contexto |
| **Coordinador** | `agents/coordinator.py` | Orquesta el pipeline |
| **Persistencia** | `agents/persistence.py` | Guarda traducción + métricas |

---

## 3. Context Agent y KV Cache (Redis)

El Context Agent mantiene el estado de la conversación por sesión, actuando como
una caché clave-valor. **Persistencia temporal configurable** vía
`CONTEXT_TTL_SECONDS` (refrescada con `EXPIRE` en cada escritura).

### Esquema de claves Redis

| Clave | Tipo | Contenido |
|-------|------|-----------|
| `ctx:{sk}:glosses` | LIST | Señas de la frase activa (buffer) |
| `ctx:{sk}:entities` | HASH | Slots: `subject`, `verb`, `place`, `time`, … |
| `ctx:{sk}:history` | LIST | Últimas `HISTORY_WINDOW` frases generadas |
| `ctx:{sk}:last_text` | STRING | Última frase (para continuaciones) |
| `ctx:{sk}:ollama_kv` | STRING | Array `context` (estado KV) que devuelve Ollama |
| `ctx:active` | SET | Sesiones activas |

`sk` (session key) = `device_uid` o `device_uid:session_id`.

### Doble nivel de KV Cache

1. **Conversacional:** `load()` recupera glosas/entidades/historial e inyecta en
   el `AgentContext`; `observe()` y `write_back()` actualizan Redis. Evita
   "empezar de cero" en cada seña.
2. **KV del modelo:** Ollama `/api/generate` devuelve un array `context` que es
   su estado KV. Se guarda en `ctx:{sk}:ollama_kv` y se reenvía como `context` en
   la siguiente llamada → reutilización real del KV cache del modelo (coherencia
   + menor latencia).

### Detección de entidades

Mapa ligero `gloss → categoría` en `ml/labels.py` (`GLOSS_CATEGORY`,
`categorize()`). Los marcadores temporales (`HOY/MAÑANA/AYER`) fijan el slot
`time`, lo que permite a Llama ajustar el tiempo verbal.

### Degradación elegante

Si Redis no está disponible, el Context Agent usa un **almacén en memoria**
(`_MEM`) con la misma semántica (sin TTL). El sistema sigue operativo.

---

## 4. Modelo de IA — Transformer temporal

`app/ml/model.py` — `SignTransformer`: entrada `[B,T,126]` → proyección a
`d_model=128` → positional encoding → 4 capas `TransformerEncoderLayer`
(8 cabezas, GELU) → pooling temporal enmascarado → MLP → `num_classes`.

`app/ml/inference.py`: singleton `InferenceEngine`. Carga `MODEL_PATH` si existe;
si no, **fallback determinista** (estable y reproducible). Vocabulario en
`ml/labels.py` (`labels.json`).

---

## 5. Modelo de datos (PostgreSQL)

```
devices (1)───(N) translation_sessions (1)───(N) translations
   └───────────────(N)───────────────────────────┘ (translations.device_id)
devices (1)───(N) usage_metrics
```

| Tabla | Campos clave |
|-------|--------------|
| `devices` | device_uid (único), label, dark_mode, confidence_threshold, context_enabled |
| `translation_sessions` | device_id, title, total_signs, started_at, ended_at |
| `translations` | device_id, session_id, glosses (JSON), natural_text, confidence, latency_ms, **used_context** |
| `usage_metrics` | device_id, event, value, avg_confidence, avg_latency_ms |

Las tablas se crean al arrancar (`init_models()`); no se requiere migración para
el primer despliegue.

---

## 6. Protocolo WebSocket

`GET /api/v1/ws/translate?device=<uuid>&session_id=<opt>`

**Cliente → Servidor:** `{type:"frame", landmarks:[126]}` · `{type:"finalize"}` · `{type:"reset"}`

**Servidor → Cliente:**
```json
{ "type": "ready",   "sequence_length": 30 }
{ "type": "partial", "gloss": "ESTUDIAR", "confidence": 0.8, "buffer": [...], "entities": {...} }
{ "type": "final",   "text": "Mañana estudiaré en la universidad.", "history": [...], "used_context": true, "latency_ms": 540 }
```

---

## 7. Frontend

Estático (HTML + TailwindCSS CDN + JS ES6), servido por Nginx (proxy de `/api` y
`/api/v1/ws`). Módulos `js/`: `config.js` (UUID de dispositivo), `api.js`
(cliente con `X-Device-Id`), `ui.js` (tema/toasts/nav), `translator.js`
(`TranslatorEngine`: WebRTC + MediaPipe + WS + auto-finalización por pausa).

Pantallas: Inicio, Traductor, Historial, Configuración, Información, y en modo
dev: Dataset y Entrenamiento (la nav las muestra según `system/info.dev_mode`).

---

## 8. Modo desarrollador

Activado con `DEV_MODE=true`. Expone:

- `GET /dev/dataset`, `POST /dev/dataset/sample` — inspeccionar clases y grabar
  muestras (`.npy` bajo `DATA_DIR/sequences/<LABEL>/`).
- `POST /dev/training/start`, `GET /dev/training/status`, `POST /dev/training/stop`
  — lanza `python -m ml_training.train` como subproceso y transmite logs.

Los endpoints validan `DEV_MODE` vía la dependencia `require_dev_mode`.

---

## 9. Pruebas

`pytest` con SQLite en memoria (override de `get_db`) y cliente `httpx`/ASGI.
Cubre seguridad de datos, preprocesamiento, inferencia, exportación, pipeline de
agentes, **Context Agent** (memoria/entidades/continuación) y endpoints REST.
Ver `backend/tests/` (22 tests).
