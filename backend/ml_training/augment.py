"""Aumento de datos para secuencias de landmarks.

Técnicas:
  - Jitter gaussiano (ruido en coordenadas).
  - Escalado aleatorio.
  - Traslación aleatoria.
  - Time-warp (re-muestreo temporal no lineal).
  - Espejado horizontal (intercambia manos y refleja x).

Uso:
    python -m ml_training.augment --factor 4
"""
from __future__ import annotations

import argparse
import os

import numpy as np

from ml_training.config import SEQUENCES_DIR

FEATURES = 126
PER_HAND = 21 * 3


def jitter(seq: np.ndarray, sigma: float = 0.01) -> np.ndarray:
    return seq + np.random.normal(0, sigma, seq.shape).astype(np.float32)


def scale(seq: np.ndarray, low: float = 0.9, high: float = 1.1) -> np.ndarray:
    return seq * np.random.uniform(low, high)


def translate(seq: np.ndarray, delta: float = 0.05) -> np.ndarray:
    shift = np.random.uniform(-delta, delta, size=(1, seq.shape[1])).astype(np.float32)
    return seq + shift


def time_warp(seq: np.ndarray) -> np.ndarray:
    T = seq.shape[0]
    src = np.linspace(0, 1, T)
    warp = np.clip(src + np.random.normal(0, 0.05, T), 0, 1)
    warp = np.sort(warp)
    out = np.zeros_like(seq)
    for c in range(seq.shape[1]):
        out[:, c] = np.interp(src, warp, seq[:, c])
    return out.astype(np.float32)


def mirror(seq: np.ndarray) -> np.ndarray:
    out = seq.copy()
    # Refleja la coordenada x (índices 0,3,6,...) -> 1 - x
    for i in range(0, FEATURES, 3):
        nz = out[:, i] != 0
        out[nz, i] = 1.0 - out[nz, i]
    # Intercambia mano izquierda/derecha
    left, right = out[:, :PER_HAND].copy(), out[:, PER_HAND:].copy()
    out[:, :PER_HAND], out[:, PER_HAND:] = right, left
    return out


AUGS = [jitter, scale, translate, time_warp, mirror]


def augment_dataset(factor: int, seq_dir: str = SEQUENCES_DIR) -> None:
    if not os.path.isdir(seq_dir):
        print(f"[augment] No existe {seq_dir}")
        return
    for label in os.listdir(seq_dir):
        cdir = os.path.join(seq_dir, label)
        if not os.path.isdir(cdir):
            continue
        originals = [f for f in os.listdir(cdir) if f.endswith(".npy") and "_aug" not in f]
        created = 0
        for fname in originals:
            base = np.load(os.path.join(cdir, fname))
            for k in range(factor):
                aug = base.copy()
                # aplica 1-2 transformaciones aleatorias
                for fn in np.random.choice(AUGS, size=np.random.randint(1, 3), replace=False):
                    aug = fn(aug)
                out_name = fname.replace(".npy", f"_aug{k+1}.npy")
                np.save(os.path.join(cdir, out_name), aug.astype(np.float32))
                created += 1
        print(f"[augment] {label}: +{created} muestras aumentadas")


def main() -> None:
    p = argparse.ArgumentParser(description="Aumento de datos LSC")
    p.add_argument("--factor", type=int, default=3, help="Muestras generadas por original")
    args = p.parse_args()
    np.random.seed(42)
    augment_dataset(args.factor)


if __name__ == "__main__":
    main()
