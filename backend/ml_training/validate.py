"""Validación de un checkpoint entrenado: matriz de confusión y métricas.

Uso:
    python -m ml_training.validate --checkpoint ml_store/lsc_transformer.pt
"""
from __future__ import annotations

import argparse

import numpy as np
import torch
from sklearn.metrics import classification_report, confusion_matrix
from torch.utils.data import DataLoader

from app.ml.model import build_model
from ml_training.config import CHECKPOINT, SEQUENCE_LENGTH
from ml_training.dataset import LSCDataset, load_samples, split_samples


def validate(checkpoint: str) -> None:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    ckpt = torch.load(checkpoint, map_location=device)
    labels = ckpt["labels"]

    model = build_model(num_classes=len(labels))
    model.load_state_dict(ckpt["model_state"])
    model.to(device).eval()

    samples = load_samples(labels)
    _, _, test_s = split_samples(samples)
    loader = DataLoader(LSCDataset(test_s, SEQUENCE_LENGTH), batch_size=32)

    y_true, y_pred = [], []
    with torch.no_grad():
        for x, mask, y in loader:
            logits = model(x.to(device), mask.to(device))
            y_pred.extend(logits.argmax(dim=-1).cpu().numpy().tolist())
            y_true.extend(y.numpy().tolist())

    if not y_true:
        print("[validate] No hay muestras de test.")
        return

    print("[validate] Reporte de clasificación:")
    print(classification_report(
        y_true, y_pred, target_names=labels, zero_division=0, digits=4
    ))
    print("[validate] Matriz de confusión:")
    print(confusion_matrix(y_true, y_pred))
    acc = float(np.mean(np.array(y_true) == np.array(y_pred)))
    print(f"[validate] accuracy de test = {acc:.4f}")


def main() -> None:
    p = argparse.ArgumentParser(description="Validación del modelo LSC")
    p.add_argument("--checkpoint", default=CHECKPOINT)
    validate(p.parse_args().checkpoint)


if __name__ == "__main__":
    main()
