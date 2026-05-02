from __future__ import annotations

import numpy as np

from .config import ChannelConfig


def add_awgn(signal: np.ndarray, config: ChannelConfig) -> tuple[np.ndarray, np.ndarray]:
    channel_signal = config.attenuation * signal + config.dc_offset
    generator = np.random.default_rng(config.random_seed)
    if not config.noise_enabled:
        noise = np.zeros_like(channel_signal)
        return channel_signal, noise

    if config.noise_std is not None:
        noise_std = float(config.noise_std)
    else:
        signal_power = float(np.mean(channel_signal**2))
        snr_linear = 10 ** (config.snr_db / 10.0)
        noise_power = signal_power / snr_linear if snr_linear > 0 else signal_power
        noise_std = float(np.sqrt(noise_power))

    noise = generator.normal(0.0, noise_std, size=signal.shape)
    return channel_signal + noise, noise
