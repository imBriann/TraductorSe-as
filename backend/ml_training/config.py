"""Configuración de rutas y parámetros del pipeline de entrenamiento."""
from __future__ import annotations

import os

DATA_DIR = os.environ.get("LSC_DATA_DIR", "data")
SEQUENCES_DIR = os.path.join(DATA_DIR, "sequences")
SPLITS_DIR = os.path.join(DATA_DIR, "splits")
LABELS_FILE = os.path.join(DATA_DIR, "labels.json")

MODEL_STORE = os.environ.get("LSC_MODEL_STORE", "ml_store")
CHECKPOINT = os.path.join(MODEL_STORE, "lsc_transformer.pt")
LABELS_OUT = os.path.join(MODEL_STORE, "labels.json")

SEQUENCE_LENGTH = int(os.environ.get("LSC_SEQUENCE_LENGTH", "30"))
SEED = 42
