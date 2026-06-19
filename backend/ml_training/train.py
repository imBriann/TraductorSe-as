"""Entrenamiento del Transformer temporal para clasificación de señas LSC.

Uso:
    python -m ml_training.train --epochs 80 --batch-size 32 --lr 3e-4
"""
from __future__ import annotations

import argparse
import json
import os

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader

from app.ml.model import build_model
from ml_training.config import CHECKPOINT, LABELS_OUT, MODEL_STORE, SEED, SEQUENCE_LENGTH
from ml_training.dataset import (
    LSCDataset,
    discover_labels,
    load_samples,
    split_samples,
)


def set_seed(seed: int = SEED) -> None:
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def evaluate(model, loader, device) -> float:
    model.eval()
    correct = total = 0
    with torch.no_grad():
        for x, mask, y in loader:
            x, mask, y = x.to(device), mask.to(device), y.to(device)
            logits = model(x, mask)
            preds = logits.argmax(dim=-1)
            correct += (preds == y).sum().item()
            total += y.size(0)
    return correct / max(total, 1)


def train(args) -> None:
    set_seed()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[train] dispositivo: {device}")

    labels = discover_labels()
    if not labels:
        raise SystemExit("[train] No se encontraron clases. Ejecuta capture.py primero.")
    samples = load_samples(labels)
    if not samples:
        raise SystemExit("[train] No hay muestras .npy en el dataset.")

    train_s, val_s, test_s = split_samples(samples)
    print(f"[train] clases={len(labels)} train={len(train_s)} "
          f"val={len(val_s)} test={len(test_s)}")

    train_loader = DataLoader(
        LSCDataset(train_s, SEQUENCE_LENGTH), batch_size=args.batch_size,
        shuffle=True, num_workers=0,
    )
    val_loader = DataLoader(
        LSCDataset(val_s, SEQUENCE_LENGTH), batch_size=args.batch_size,
    )
    test_loader = DataLoader(
        LSCDataset(test_s, SEQUENCE_LENGTH), batch_size=args.batch_size,
    )

    model = build_model(num_classes=len(labels)).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)
    criterion = nn.CrossEntropyLoss(label_smoothing=0.05)

    os.makedirs(MODEL_STORE, exist_ok=True)
    best_val = 0.0

    for epoch in range(1, args.epochs + 1):
        model.train()
        running = 0.0
        for x, mask, y in train_loader:
            x, mask, y = x.to(device), mask.to(device), y.to(device)
            optimizer.zero_grad()
            logits = model(x, mask)
            loss = criterion(logits, y)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            running += loss.item() * y.size(0)
        scheduler.step()

        train_loss = running / max(len(train_s), 1)
        val_acc = evaluate(model, val_loader, device)
        print(f"[train] epoch {epoch:>3}/{args.epochs}  "
              f"loss={train_loss:.4f}  val_acc={val_acc:.4f}")

        if val_acc >= best_val:
            best_val = val_acc
            torch.save(
                {"model_state": model.state_dict(), "labels": labels,
                 "seq_len": SEQUENCE_LENGTH, "val_acc": val_acc},
                CHECKPOINT,
            )
            with open(LABELS_OUT, "w", encoding="utf-8") as fh:
                json.dump({"labels": labels}, fh, ensure_ascii=False, indent=2)

    test_acc = evaluate(model, test_loader, device)
    print(f"[train] mejor val_acc={best_val:.4f}  test_acc={test_acc:.4f}")
    print(f"[train] checkpoint -> {CHECKPOINT}")


def main() -> None:
    p = argparse.ArgumentParser(description="Entrenamiento Transformer LSC")
    p.add_argument("--epochs", type=int, default=80)
    p.add_argument("--batch-size", type=int, default=32)
    p.add_argument("--lr", type=float, default=3e-4)
    train(p.parse_args())


if __name__ == "__main__":
    main()
