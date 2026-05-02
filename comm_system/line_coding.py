from __future__ import annotations

import numpy as np

from .config import LineCodeConfig


def encode_line(bits: np.ndarray, config: LineCodeConfig) -> np.ndarray:
    scheme = config.scheme.lower()

    if scheme == "on_off":
        return np.where(bits == 1, config.one_level, config.zero_level).astype(float)

    if scheme == "polar":
        return np.where(bits == 1, config.one_level, config.zero_level).astype(float)

    if scheme == "bipolar":
        levels = np.full(bits.shape, config.bipolar_zero_level, dtype=float)
        polarity = 1.0 if config.bipolar_first_mark_positive else -1.0
        for idx, bit in enumerate(bits):
            if bit == 1:
                levels[idx] = polarity * config.one_level
                polarity *= -1.0
        return levels

    raise ValueError(f"Unsupported line code scheme: {config.scheme}")
