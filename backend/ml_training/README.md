# Pipeline de Dataset y Entrenamiento — LSC i5.0

Estructura de datos esperada:

```
data/
├── raw/                      # vídeos / capturas crudas (opcional)
├── sequences/                # .npy por muestra: shape [T, 126]
│   ├── HOLA/
│   │   ├── HOLA_0001.npy
│   │   └── ...
│   ├── GRACIAS/
│   └── ...
├── labels.json               # {"labels": ["HOLA", "GRACIAS", ...]}
└── splits/                   # índices train/val/test generados por dataset.py
```

## Flujo completo

```bash
# 1. Capturar muestras desde la webcam (genera .npy en data/sequences/<ETIQUETA>/)
python -m ml_training.capture --label HOLA --samples 40

# 2. (Opcional) Etiquetar/validar muestras capturadas
python -m ml_training.label --review data/sequences

# 3. Aumentar datos (jitter, escala, time-warp)
python -m ml_training.augment --factor 4

# 4. Entrenar el Transformer
python -m ml_training.train --epochs 80 --batch-size 32

# 5. Validar el modelo entrenado
python -m ml_training.validate --checkpoint ml_store/lsc_transformer.pt
```

El checkpoint resultante (`ml_store/lsc_transformer.pt`) y `ml_store/labels.json`
son consumidos automáticamente por el `InferenceEngine` del backend.
