from __future__ import annotations

from pathlib import Path

import numpy as np

from comm_system.config import SimulationConfig, build_config
from comm_system.pipeline import run_simulation


def configure_simulation(scheme: str = "polar") -> SimulationConfig:
    # Signalling scheme: "on_off", "polar", or "bipolar"
    config = build_config(scheme)

    # Source block: control the analog input signal here.
    config.source.waveform = "multi_tone"  # "sine", "cosine", "square", "multi_tone"
    config.source.amplitude = 1.0
    config.source.frequency_hz = 5.0
    config.source.phase_rad = np.pi / 8
    config.source.secondary_amplitude = 0.35
    config.source.secondary_frequency_hz = 13.0
    config.source.secondary_phase_rad = np.pi / 5
    config.source.dc_offset = 0.0
    config.source.duration_s = 1.0
    config.source.analog_sample_rate_hz = None
    config.source.analog_oversample_factor = 40

    # Sampling block.
    config.sampling.sampling_rate_hz = 80.0
    config.sampling.sample_phase_s = 0.0

    # Quantizer block.
    # Use either bits_per_sample or quantization_levels.
    config.quantizer.bits_per_sample = 4
    config.quantizer.quantization_levels = None
    # Example alternative:
    # config.quantizer.bits_per_sample = None
    # config.quantizer.quantization_levels = 12
    config.quantizer.min_value = -1.5
    config.quantizer.max_value = 1.5

    # Line-coding block.
    config.line_code.one_level = 1.0
    config.line_code.bipolar_zero_level = 0.0
    config.line_code.bipolar_first_mark_positive = True

    # Pulse-shaping block: "rectangular", "half_sine", or "raised_cosine"
    config.pulse_shape.pulse = "rectangular"
    config.pulse_shape.samples_per_symbol = 32
    config.pulse_shape.amplitude = 1.0
    config.pulse_shape.rolloff = 0.35
    config.pulse_shape.span_symbols = 6

    # Channel block.
    config.channel.noise_enabled = True
    config.channel.snr_db = 18.0
    config.channel.noise_std = None
    config.channel.attenuation = 1.0
    config.channel.dc_offset = 0.0
    config.channel.random_seed = 7

    # Receiver block.
    config.receiver.sample_offset = 0
    config.receiver.normalize_threshold_to_pulse_energy = True
    config.receiver.bipolar_use_absolute_value = True

    if config.line_code.scheme == "on_off":
        config.line_code.zero_level = 0.0
        config.receiver.decision_threshold = 0.5
    elif config.line_code.scheme == "polar":
        config.line_code.zero_level = -1.0
        config.receiver.decision_threshold = 0.0
    elif config.line_code.scheme == "bipolar":
        config.line_code.zero_level = 0.0
        config.receiver.decision_threshold = 0.5
    else:
        raise ValueError(f"Unsupported signalling scheme: {config.line_code.scheme}")

    # Output + plotting block.
    config.output.root_dir = Path("artifacts")
    config.output.save_text = True
    config.output.save_plots = False
    config.output.show_plots = True
    config.output.plot_backend = "matplotlib"  # "matplotlib" or "seaborn"
    config.output.plot_style = "default"  # e.g. "default", "ggplot", "dark_background", "darkgrid"
    config.output.seaborn_context = "notebook"
    config.output.seaborn_palette = "deep"
    config.output.figure_dpi = 160
    config.output.eye_symbols = 2
    config.output.eye_trace_count = 120
    config.output.bitstream_preview_bits = 128
    config.output.close_after_show = False

    return config


def main() -> None:
    config = configure_simulation()
    metrics = run_simulation(config)

    print("Simulation completed")
    print(f"Scheme              : {metrics['scheme']}")
    print(f"Sample count        : {metrics['sample_count']}")
    print(f"Quantizer bits      : {metrics['bits_per_sample']}")
    print(f"Quantizer levels    : {metrics['quantization_levels']}")
    print(f"Bitstream length    : {metrics['bitstream_length']}")
    print(f"Samples per symbol  : {metrics['samples_per_symbol']}")
    print(f"SNR (dB)            : {metrics['snr_db']}")
    print(f"BER                 : {metrics['ber']:.6f}")
    print(f"Artifacts directory : {metrics['artifacts_dir']}")


if __name__ == "__main__":
    main()
