from __future__ import annotations

import math

import numpy as np

from .config import QuantizerConfig


def quantize_samples(
    samples: np.ndarray,
    config: QuantizerConfig,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    levels, bits_per_sample = resolve_quantizer_settings(config)
    clipped = np.clip(samples, config.min_value, config.max_value)
    step = (config.max_value - config.min_value) / (levels - 1)
    indices = np.rint((clipped - config.min_value) / step).astype(int)
    quantized = config.min_value + indices * step
    return quantized, indices, _build_codebook(indices, bits_per_sample)


def _build_codebook(indices: np.ndarray, bits_per_sample: int) -> np.ndarray:
    return np.array(
        [list(np.binary_repr(index, width=bits_per_sample)) for index in indices],
        dtype="<U1",
    )


def build_bitstream(words: np.ndarray) -> np.ndarray:
    return words.astype(int).reshape(-1)


def resolve_quantizer_settings(config: QuantizerConfig) -> tuple[int, int]:
    if config.quantization_levels is not None:
        levels = int(config.quantization_levels)
    elif config.bits_per_sample is not None:
        levels = 2 ** int(config.bits_per_sample)
    else:
        raise ValueError("Set either bits_per_sample or quantization_levels")

    if levels < 2:
        raise ValueError("Quantizer must have at least 2 levels")

    if config.bits_per_sample is None:
        bits_per_sample = math.ceil(math.log2(levels))
    else:
        bits_per_sample = int(config.bits_per_sample)

    if bits_per_sample < 1:
        raise ValueError("bits_per_sample must be at least 1")
    if 2**bits_per_sample < levels:
        raise ValueError("bits_per_sample is too small for the requested quantization_levels")
    if config.max_value <= config.min_value:
        raise ValueError("quantizer max_value must be greater than min_value")

    return levels, bits_per_sample
