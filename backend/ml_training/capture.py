"""Captura de muestras de señas desde la webcam usando MediaPipe Hands.

Cada muestra es una secuencia de SEQUENCE_LENGTH frames; cada frame es un
vector de 126 floats (2 manos x 21 landmarks x 3 coords). Se guarda como .npy
en data/sequences/<ETIQUETA>/.

Uso:
    python -m ml_training.capture --label HOLA --samples 40 --seq-len 30
"""
from __future__ import annotations

import argparse
import os
import time

import numpy as np

from ml_training.config import SEQUENCES_DIR, SEQUENCE_LENGTH

FEATURES = 126


def _extract(hand_landmarks_list, num_hands: int = 2) -> np.ndarray:
    vec = np.zeros(FEATURES, dtype=np.float32)
    if hand_landmarks_list:
        for h, hand in enumerate(hand_landmarks_list[:num_hands]):
            base = h * 21 * 3
            for i, lm in enumerate(hand.landmark):
                off = base + i * 3
                vec[off], vec[off + 1], vec[off + 2] = lm.x, lm.y, lm.z
    return vec


def capture(label: str, samples: int, seq_len: int, countdown: int = 3) -> None:
    import cv2
    import mediapipe as mp

    out_dir = os.path.join(SEQUENCES_DIR, label.upper())
    os.makedirs(out_dir, exist_ok=True)
    existing = len([f for f in os.listdir(out_dir) if f.endswith(".npy")])

    mp_hands = mp.solutions.hands
    mp_draw = mp.solutions.drawing_utils
    cap = cv2.VideoCapture(0)

    with mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.6,
                        min_tracking_confidence=0.6) as hands:
        for s in range(samples):
            # Cuenta atrás
            for c in range(countdown, 0, -1):
                ret, frame = cap.read()
                if not ret:
                    continue
                cv2.putText(frame, f"{label} {s+1}/{samples} en {c}", (30, 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)
                cv2.imshow("Captura LSC", frame)
                cv2.waitKey(1)
                time.sleep(1)

            sequence = []
            while len(sequence) < seq_len:
                ret, frame = cap.read()
                if not ret:
                    break
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                res = hands.process(rgb)
                sequence.append(_extract(res.multi_hand_landmarks))
                if res.multi_hand_landmarks:
                    for hl in res.multi_hand_landmarks:
                        mp_draw.draw_landmarks(frame, hl, mp_hands.HAND_CONNECTIONS)
                cv2.putText(frame, f"Grabando {len(sequence)}/{seq_len}", (30, 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 200, 0), 2)
                cv2.imshow("Captura LSC", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    cap.release()
                    cv2.destroyAllWindows()
                    return

            arr = np.asarray(sequence[:seq_len], dtype=np.float32)
            idx = existing + s + 1
            path = os.path.join(out_dir, f"{label.upper()}_{idx:04d}.npy")
            np.save(path, arr)
            print(f"[capture] guardado {path}  shape={arr.shape}")

    cap.release()
    cv2.destroyAllWindows()


def main() -> None:
    p = argparse.ArgumentParser(description="Captura muestras de señas LSC")
    p.add_argument("--label", required=True, help="Etiqueta de la seña (ej: HOLA)")
    p.add_argument("--samples", type=int, default=30)
    p.add_argument("--seq-len", type=int, default=SEQUENCE_LENGTH)
    args = p.parse_args()
    capture(args.label, args.samples, args.seq_len)


if __name__ == "__main__":
    main()
