from __future__ import annotations

import numpy as np

from .config import PulseShapeConfig


def build_pulse(config: PulseShapeConfig) -> np.ndarray:
    pulse_name = config.pulse.lower()

    if pulse_name in {"rectangular", "nrz"}:
        return np.full(config.samples_per_symbol, config.amplitude, dtype=float)

    if pulse_name == "rz":
        return _build_rz(config)

    if pulse_name == "half_sine":
        time = np.linspace(0.0, np.pi, config.samples_per_symbol, endpoint=False)
        pulse = np.sin(time)
        return _normalize_pulse(pulse, config.amplitude)

    if pulse_name in {"raised_cosine", "rc"}:
        return _build_raised_cosine(config)

    if pulse_name == "sinc":
        return _build_sinc(config)

    raise ValueError(f"Unsupported pulse shape: {config.pulse}")


def shape_symbols(
    symbols: np.ndarray,
    pulse: np.ndarray,
    samples_per_symbol: int,
) -> tuple[np.ndarray, np.ndarray]:
    upsampled = np.zeros(len(symbols) * samples_per_symbol, dtype=float)
    upsampled[::samples_per_symbol] = symbols
    waveform = np.convolve(upsampled, pulse, mode="full")
    return upsampled, waveform


def _build_raised_cosine(config: PulseShapeConfig) -> np.ndarray:
    if not 0.0 <= config.rolloff <= 1.0:
        raise ValueError("rolloff must be between 0 and 1 for raised_cosine")
    if config.span_symbols < 1:
        raise ValueError("span_symbols must be at least 1")

    sps = config.samples_per_symbol
    span = config.span_symbols
    rolloff = config.rolloff
    time = np.arange(-span * sps / 2, span * sps / 2 + 1, dtype=float) / sps
    pulse = np.zeros_like(time)

    for index, sample in enumerate(time):
        if np.isclose(sample, 0.0):
            pulse[index] = 1.0
            continue

        if rolloff != 0.0 and np.isclose(abs(sample), 1.0 / (2.0 * rolloff)):
            pulse[index] = (np.pi / 4.0) * np.sinc(1.0 / (2.0 * rolloff))
            continue

        numerator = np.sinc(sample) * np.cos(np.pi * rolloff * sample)
        denominator = 1.0 - (2.0 * rolloff * sample) ** 2
        pulse[index] = numerator / denominator

    return _normalize_pulse(pulse, config.amplitude)


def _build_sinc(config: PulseShapeConfig) -> np.ndarray:
    if config.span_symbols < 1:
        raise ValueError("span_symbols must be at least 1")

    sps = config.samples_per_symbol
    span = config.span_symbols
    time = np.arange(-span * sps / 2, span * sps / 2 + 1, dtype=float) / sps
    pulse = np.sinc(time)
    return _normalize_pulse(pulse, config.amplitude)


def _build_rz(config: PulseShapeConfig) -> np.ndarray:
    if not 0.0 < config.rz_duty_cycle <= 1.0:
        raise ValueError("rz_duty_cycle must be greater than 0 and at most 1")

    pulse = np.zeros(config.samples_per_symbol, dtype=float)
    active_samples = max(1, int(round(config.samples_per_symbol * config.rz_duty_cycle)))
    pulse[:active_samples] = config.amplitude
    return pulse


def _normalize_pulse(pulse: np.ndarray, amplitude: float) -> np.ndarray:
    peak = np.max(np.abs(pulse))
    if peak == 0.0:
        raise ValueError("Pulse normalization failed because the pulse peak is zero")
    return amplitude * pulse / peak
