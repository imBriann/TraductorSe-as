"""Constantes compartidas del pipeline de visión / ML."""

# MediaPipe Hands produce 21 landmarks por mano, cada uno con (x, y, z).
LANDMARKS_PER_HAND = 21
COORDS_PER_LANDMARK = 3
HANDS = 2

# Vector de características por frame: 2 manos * 21 puntos * 3 coords = 126
FEATURES_PER_FRAME = HANDS * LANDMARKS_PER_HAND * COORDS_PER_LANDMARK  # 126

# Longitud por defecto de la secuencia temporal (frames)
DEFAULT_SEQUENCE_LENGTH = 30
