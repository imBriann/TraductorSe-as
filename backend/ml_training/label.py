"""Etiquetado / revisión del dataset.

Genera (o actualiza) data/labels.json a partir de los subdirectorios de
data/sequences/, y reporta el conteo de muestras por etiqueta para validar el
balance del dataset.

Uso:
    python -m ml_training.label --review data/sequences
    python -m ml_training.label --rename HOLA SALUDO   # renombra una clase
"""
from __future__ import annotations

import argparse
import json
import os
import shutil

from ml_training.config import LABELS_FILE, SEQUENCES_DIR


def build_labels(seq_dir: str = SEQUENCES_DIR) -> list[str]:
    if not os.path.isdir(seq_dir):
        print(f"[label] No existe {seq_dir}")
        return []
    labels = sorted(
        d for d in os.listdir(seq_dir) if os.path.isdir(os.path.join(seq_dir, d))
    )
    os.makedirs(os.path.dirname(LABELS_FILE) or ".", exist_ok=True)
    with open(LABELS_FILE, "w", encoding="utf-8") as fh:
        json.dump({"labels": labels}, fh, ensure_ascii=False, indent=2)
    return labels


def review(seq_dir: str = SEQUENCES_DIR) -> None:
    labels = build_labels(seq_dir)
    print(f"[label] {len(labels)} clases detectadas:")
    total = 0
    for lab in labels:
        n = len([f for f in os.listdir(os.path.join(seq_dir, lab)) if f.endswith(".npy")])
        total += n
        flag = "  ⚠ pocas muestras" if n < 15 else ""
        print(f"  - {lab:<16} {n:>4} muestras{flag}")
    print(f"[label] Total: {total} muestras en {len(labels)} clases")
    print(f"[label] labels.json -> {LABELS_FILE}")


def rename(old: str, new: str, seq_dir: str = SEQUENCES_DIR) -> None:
    src = os.path.join(seq_dir, old.upper())
    dst = os.path.join(seq_dir, new.upper())
    if not os.path.isdir(src):
        print(f"[label] No existe la clase {old}")
        return
    shutil.move(src, dst)
    build_labels(seq_dir)
    print(f"[label] {old} -> {new}")


def main() -> None:
    p = argparse.ArgumentParser(description="Etiquetado/revisión del dataset LSC")
    p.add_argument("--review", nargs="?", const=SEQUENCES_DIR, help="Revisar dataset")
    p.add_argument("--rename", nargs=2, metavar=("OLD", "NEW"))
    args = p.parse_args()

    if args.rename:
        rename(*args.rename)
    else:
        review(args.review or SEQUENCES_DIR)


if __name__ == "__main__":
    main()
