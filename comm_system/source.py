from __future__ import annotations

import numpy as np

from .config import SourceConfig, SamplingConfig


def generate_analog_signal(config: SourceConfig) -> tuple[np.ndarray, np.ndarray]:
    analog_sample_rate_hz = _resolve_analog_sample_rate(config)
    dt = 1.0 / analog_sample_rate_hz
    time = np.arange(0.0, config.duration_s + 0.5 * dt, dt)
    time = time[time <= config.duration_s]

    if config.waveform == "sine":
        signal = config.amplitude * np.sin(
            2.0 * np.pi * config.frequency_hz * time + config.phase_rad
        )
    elif config.waveform == "cosine":
        signal = config.amplitude * np.cos(
            2.0 * np.pi * config.frequency_hz * time + config.phase_rad
        )
    elif config.waveform == "square":
        base = np.sin(2.0 * np.pi * config.frequency_hz * time + config.phase_rad)
        signal = config.amplitude * np.where(base >= 0.0, 1.0, -1.0)
    elif config.waveform == "multi_tone":
        primary = config.amplitude * np.sin(
            2.0 * np.pi * config.frequency_hz * time + config.phase_rad
        )
        secondary = config.secondary_amplitude * np.sin(
            2.0 * np.pi * config.secondary_frequency_hz * time + config.secondary_phase_rad
        )
        signal = primary + secondary
    else:
        raise ValueError(f"Unsupported source waveform: {config.waveform}")

    signal = signal + config.dc_offset
    return time, signal


def sample_signal(
    analog_time: np.ndarray,
    analog_signal: np.ndarray,
    config: SamplingConfig,
) -> tuple[np.ndarray, np.ndarray]:
    sample_period = 1.0 / config.sampling_rate_hz
    sample_time = np.arange(
        config.sample_phase_s,
        analog_time[-1] + 0.5 * sample_period,
        sample_period,
    )
    sample_time = sample_time[sample_time <= analog_time[-1]]
    sampled = np.interp(sample_time, analog_time, analog_signal)
    return sample_time, sampled


def _resolve_analog_sample_rate(config: SourceConfig) -> float:
    if config.analog_sample_rate_hz is not None:
        if config.analog_sample_rate_hz <= 0:
            raise ValueError("analog_sample_rate_hz must be positive")
        return config.analog_sample_rate_hz

    dominant_frequency = max(abs(config.frequency_hz), abs(config.secondary_frequency_hz), 1.0)
    sample_rate = dominant_frequency * config.analog_oversample_factor
    if sample_rate <= 0:
        raise ValueError("Resolved analog sample rate must be positive")
    return sample_rate
