"""Dataset PyTorch para secuencias de landmarks LSC."""
from __future__ import annotations

import json
import os
from typing import List, Tuple

import numpy as np
import torch
from torch.utils.data import Dataset

from ml_training.config import LABELS_FILE, SEQUENCES_DIR, SEQUENCE_LENGTH

FEATURES = 126


def _pad_or_truncate(seq: np.ndarray, seq_len: int) -> Tuple[np.ndarray, np.ndarray]:
    T = seq.shape[0]
    mask = np.zeros((seq_len,), dtype=bool)
    if T >= seq_len:
        seq = seq[-seq_len:]
    else:
        pad = np.zeros((seq_len - T, FEATURES), dtype=np.float32)
        seq = np.concatenate([seq, pad], axis=0)
        mask[T:] = True
    return seq.astype(np.float32), mask


def discover_labels(seq_dir: str = SEQUENCES_DIR) -> List[str]:
    if os.path.exists(LABELS_FILE):
        with open(LABELS_FILE, "r", encoding="utf-8") as fh:
            return json.load(fh)["labels"]
    return sorted(
        d for d in os.listdir(seq_dir) if os.path.isdir(os.path.join(seq_dir, d))
    )


class LSCDataset(Dataset):
    def __init__(self, samples: List[Tuple[str, int]], seq_len: int = SEQUENCE_LENGTH):
        self.samples = samples
        self.seq_len = seq_len

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int):
        path, label = self.samples[idx]
        seq = np.load(path).astype(np.float32)
        if seq.ndim == 1:
            seq = seq.reshape(1, -1)
        if seq.shape[1] != FEATURES:
            fixed = np.zeros((seq.shape[0], FEATURES), dtype=np.float32)
            n = min(seq.shape[1], FEATURES)
            fixed[:, :n] = seq[:, :n]
            seq = fixed
        seq, mask = _pad_or_truncate(seq, self.seq_len)
        return (
            torch.from_numpy(seq),
            torch.from_numpy(mask),
            torch.tensor(label, dtype=torch.long),
        )


def load_samples(labels: List[str], seq_dir: str = SEQUENCES_DIR):
    samples: List[Tuple[str, int]] = []
    for i, lab in enumerate(labels):
        cdir = os.path.join(seq_dir, lab)
        if not os.path.isdir(cdir):
            continue
        for f in os.listdir(cdir):
            if f.endswith(".npy"):
                samples.append((os.path.join(cdir, f), i))
    return samples


def split_samples(samples, val_ratio=0.15, test_ratio=0.15, seed=42):
    rng = np.random.default_rng(seed)
    idx = rng.permutation(len(samples))
    n_test = int(len(samples) * test_ratio)
    n_val = int(len(samples) * val_ratio)
    test = [samples[i] for i in idx[:n_test]]
    val = [samples[i] for i in idx[n_test:n_test + n_val]]
    train = [samples[i] for i in idx[n_test + n_val:]]
    return train, val, test
