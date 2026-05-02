from __future__ import annotations

import numpy as np

from .config import LineCodeConfig, PulseShapeConfig, ReceiverConfig


def matched_filter_receive(
    received_waveform: np.ndarray,
    pulse: np.ndarray,
    pulse_config: PulseShapeConfig,
    receiver_config: ReceiverConfig,
) -> tuple[np.ndarray, np.ndarray]:
    matched = np.convolve(received_waveform, pulse[::-1], mode="full")
    # For a pulse-shaped symbol stream, the first symbol peak appears after the
    # matched-filter delay only, not after an extra symbol interval.
    base_index = len(pulse) - 1
    decision_index = base_index + receiver_config.sample_offset
    sample_points = decision_index + np.arange(
        0, len(received_waveform), pulse_config.samples_per_symbol
    )
    sample_points = sample_points[sample_points < len(matched)]
    samples = matched[sample_points]
    return matched, samples


def decide_bits(
    symbol_samples: np.ndarray,
    line_config: LineCodeConfig,
    receiver_config: ReceiverConfig,
    pulse_energy: float,
) -> np.ndarray:
    scheme = line_config.scheme.lower()
    threshold_scale = pulse_energy if receiver_config.normalize_threshold_to_pulse_energy else 1.0

    if scheme == "on_off":
        threshold = receiver_config.decision_threshold * threshold_scale
        return (symbol_samples >= threshold).astype(int)

    if scheme == "polar":
        threshold = receiver_config.decision_threshold * threshold_scale
        return (symbol_samples >= threshold).astype(int)

    if scheme == "bipolar":
        threshold = receiver_config.decision_threshold * threshold_scale
        if receiver_config.bipolar_use_absolute_value:
            return (np.abs(symbol_samples) >= threshold).astype(int)
        return (symbol_samples >= threshold).astype(int)

    raise ValueError(f"Unsupported signalling scheme: {line_config.scheme}")


def bit_error_rate(reference_bits: np.ndarray, recovered_bits: np.ndarray) -> float:
    limit = min(len(reference_bits), len(recovered_bits))
    if limit == 0:
        return 0.0
    return float(np.mean(reference_bits[:limit] != recovered_bits[:limit]))
