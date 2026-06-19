"""Transformer temporal para clasificación de señas a partir de landmarks.

Arquitectura:
    [B, T, F] landmarks
      -> proyección lineal a d_model
      -> + positional encoding
      -> N capas TransformerEncoder (self-attention)
      -> pooling temporal (media enmascarada)
      -> cabeza de clasificación -> logits [B, num_classes]
"""
from __future__ import annotations

import math

import torch
import torch.nn as nn

from app.ml.constants import FEATURES_PER_FRAME


class PositionalEncoding(nn.Module):
    def __init__(self, d_model: int, max_len: int = 512) -> None:
        super().__init__()
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(
            torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model)
        )
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        self.register_buffer("pe", pe.unsqueeze(0))  # [1, max_len, d_model]

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x + self.pe[:, : x.size(1)]


class SignTransformer(nn.Module):
    def __init__(
        self,
        num_classes: int,
        input_dim: int = FEATURES_PER_FRAME,
        d_model: int = 128,
        nhead: int = 8,
        num_layers: int = 4,
        dim_feedforward: int = 256,
        dropout: float = 0.2,
        max_len: int = 512,
    ) -> None:
        super().__init__()
        self.input_dim = input_dim
        self.d_model = d_model
        self.num_classes = num_classes

        self.input_proj = nn.Linear(input_dim, d_model)
        self.pos_encoder = PositionalEncoding(d_model, max_len)

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
            batch_first=True,
            activation="gelu",
        )
        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        self.norm = nn.LayerNorm(d_model)
        self.head = nn.Sequential(
            nn.Dropout(dropout),
            nn.Linear(d_model, d_model // 2),
            nn.GELU(),
            nn.Linear(d_model // 2, num_classes),
        )

    def forward(
        self, x: torch.Tensor, mask: torch.Tensor | None = None
    ) -> torch.Tensor:
        # x: [B, T, F] ; mask: [B, T] (True = padding)
        h = self.input_proj(x)
        h = self.pos_encoder(h)
        h = self.encoder(h, src_key_padding_mask=mask)
        h = self.norm(h)

        if mask is not None:
            valid = (~mask).unsqueeze(-1).float()  # [B, T, 1]
            summed = (h * valid).sum(dim=1)
            counts = valid.sum(dim=1).clamp(min=1.0)
            pooled = summed / counts
        else:
            pooled = h.mean(dim=1)

        return self.head(pooled)


def build_model(num_classes: int, **kwargs) -> SignTransformer:
    return SignTransformer(num_classes=num_classes, **kwargs)
