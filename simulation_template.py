from __future__ import annotations

from pathlib import Path

import numpy as np

from comm_system.config import SimulationConfig, build_config
from comm_system.pipeline import run_simulation


def create_config(scheme: str = "polar") -> SimulationConfig:
    """Create the base simulation config.

    Supported schemes: "on_off", "polar", "bipolar".
    """
    return build_config(scheme)


def set_source_signal(
    config: SimulationConfig,
    waveform: str = "multi_tone",
    amplitude: float = 1.0,
    frequency_hz: float = 5.0,
    phase_rad: float = np.pi / 8,
    secondary_amplitude: float = 0.35,
    secondary_frequency_hz: float = 13.0,
    secondary_phase_rad: float = np.pi / 5,
    dc_offset: float = 0.0,
    duration_s: float = 1.0,
    analog_oversample_factor: int = 40,
) -> SimulationConfig:
    """Set analog input/source signal variables."""
    config.source.waveform = waveform
    config.source.amplitude = amplitude
    config.source.frequency_hz = frequency_hz
    config.source.phase_rad = phase_rad
    config.source.secondary_amplitude = secondary_amplitude
    config.source.secondary_frequency_hz = secondary_frequency_hz
    config.source.secondary_phase_rad = secondary_phase_rad
    config.source.dc_offset = dc_offset
    config.source.duration_s = duration_s
    config.source.analog_sample_rate_hz = None
    config.source.analog_oversample_factor = analog_oversample_factor
    return config


def set_sampling(
    config: SimulationConfig,
    sampling_rate_hz: float = 80.0,
    sample_phase_s: float = 0.0,
) -> SimulationConfig:
    """Set sampling block variables."""
    config.sampling.sampling_rate_hz = sampling_rate_hz
    config.sampling.sample_phase_s = sample_phase_s
    return config


def set_quantization(
    config: SimulationConfig,
    bits_per_sample: int | None = 4,
    quantization_levels: int | None = None,
    min_value: float = -1.5,
    max_value: float = 1.5,
) -> SimulationConfig:
    """Set quantizer variables.

    Use either bits_per_sample or quantization_levels.
    """
    config.quantizer.bits_per_sample = bits_per_sample
    config.quantizer.quantization_levels = quantization_levels
    config.quantizer.min_value = min_value
    config.quantizer.max_value = max_value
    return config


def set_line_coding(
    config: SimulationConfig,
    one_level: float = 1.0,
    zero_level: float | None = None,
    bipolar_zero_level: float = 0.0,
    bipolar_first_mark_positive: bool = True,
    decision_threshold: float | None = None,
) -> SimulationConfig:
    """Set line-coding variables for the selected scheme."""
    scheme = config.line_code.scheme.lower()
    config.line_code.one_level = one_level
    config.line_code.bipolar_zero_level = bipolar_zero_level
    config.line_code.bipolar_first_mark_positive = bipolar_first_mark_positive

    if scheme == "on_off":
        config.line_code.zero_level = 0.0 if zero_level is None else zero_level
        config.receiver.decision_threshold = 0.5 if decision_threshold is None else decision_threshold
    elif scheme == "polar":
        config.line_code.zero_level = -one_level if zero_level is None else zero_level
        config.receiver.decision_threshold = 0.0 if decision_threshold is None else decision_threshold
    elif scheme == "bipolar":
        config.line_code.zero_level = 0.0 if zero_level is None else zero_level
        config.receiver.decision_threshold = 0.5 if decision_threshold is None else decision_threshold
    else:
        raise ValueError(f"Unsupported signalling scheme: {scheme}")

    return config


def set_pulse_shaping(
    config: SimulationConfig,
    pulse: str = "nrz",
    samples_per_symbol: int = 32,
    amplitude: float = 1.0,
    rolloff: float = 0.35,
    span_symbols: int = 6,
    rz_duty_cycle: float = 0.5,
) -> SimulationConfig:
    """Set pulse-shaping variables."""
    config.pulse_shape.pulse = pulse
    config.pulse_shape.samples_per_symbol = samples_per_symbol
    config.pulse_shape.amplitude = amplitude
    config.pulse_shape.rolloff = rolloff
    config.pulse_shape.span_symbols = span_symbols
    config.pulse_shape.rz_duty_cycle = rz_duty_cycle
    return config


def set_channel(
    config: SimulationConfig,
    noise_enabled: bool = True,
    snr_db: float = 18.0,
    noise_std: float | None = None,
    attenuation: float = 1.0,
    dc_offset: float = 0.0,
    random_seed: int = 7,
) -> SimulationConfig:
    """Set AWGN channel variables."""
    config.channel.noise_enabled = noise_enabled
    config.channel.snr_db = snr_db
    config.channel.noise_std = noise_std
    config.channel.attenuation = attenuation
    config.channel.dc_offset = dc_offset
    config.channel.random_seed = random_seed
    return config


def set_receiver(
    config: SimulationConfig,
    sample_offset: int = 0,
    normalize_threshold_to_pulse_energy: bool = True,
    bipolar_use_absolute_value: bool = True,
) -> SimulationConfig:
    """Set receiver decision variables."""
    config.receiver.sample_offset = sample_offset
    config.receiver.normalize_threshold_to_pulse_energy = normalize_threshold_to_pulse_energy
    config.receiver.bipolar_use_absolute_value = bipolar_use_absolute_value
    return config


def set_output(
    config: SimulationConfig,
    root_dir: str | Path = "artifacts",
    save_text: bool = True,
    save_plots: bool = True,
    show_plots: bool = False,
    plot_backend: str = "matplotlib",
    plot_style: str = "default",
    figure_dpi: int = 160,
    eye_symbols: int = 2,
    eye_trace_count: int = 120,
    bitstream_preview_bits: int = 128,
) -> SimulationConfig:
    """Set result export and plotting variables."""
    config.output.root_dir = Path(root_dir)
    config.output.save_text = save_text
    config.output.save_plots = save_plots
    config.output.show_plots = show_plots
    config.output.plot_backend = plot_backend
    config.output.plot_style = plot_style
    config.output.figure_dpi = figure_dpi
    config.output.eye_symbols = eye_symbols
    config.output.eye_trace_count = eye_trace_count
    config.output.bitstream_preview_bits = bitstream_preview_bits
    config.output.close_after_show = not show_plots
    return config


def set_ber_waterfall(
    config: SimulationConfig,
    enabled: bool = False,
    snr_db_values: list[float] | None = None,
    min_bit_count: int = 100_000,
    random_seed: int = 99,
    bit_source: str = "random",
) -> SimulationConfig:
    """Set BER-vs-SNR waterfall curve variables."""
    config.ber_curve.enabled = enabled
    config.ber_curve.snr_db_values = (
        [-8, -6, -4, -2, 0, 2, 4, 6, 8, 10, 12]
        if snr_db_values is None
        else snr_db_values
    )
    config.ber_curve.min_bit_count = min_bit_count
    config.ber_curve.random_seed = random_seed
    config.ber_curve.bit_source = bit_source
    return config


def build_my_simulation() -> SimulationConfig:
    """Edit this function to control the full project from one file."""
    config = create_config(scheme="polar")

    set_source_signal(
        config,
        waveform="multi_tone",
        amplitude=1.0,
        frequency_hz=5.0,
        secondary_amplitude=0.35,
        secondary_frequency_hz=13.0,
        duration_s=1.0,
    )
    set_sampling(config, sampling_rate_hz=80.0)
    set_quantization(config, bits_per_sample=4, min_value=-1.5, max_value=1.5)
    set_line_coding(config, one_level=1.0)
    set_pulse_shaping(
        config,
        pulse="raised_cosine",
        samples_per_symbol=32,
        rolloff=0.35,
        span_symbols=6,
    )
    set_channel(config, noise_enabled=True, snr_db=18.0, random_seed=7)
    set_receiver(config, sample_offset=0)
    set_output(config, save_plots=True, show_plots=False)
    set_ber_waterfall(
        config,
        enabled=True,
        snr_db_values=[-8, -6, -4, -2, 0, 2, 4, 6, 8, 10, 12],
        min_bit_count=100_000,
        bit_source="random",
    )

    return config


def main() -> None:
    config = build_my_simulation()
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
    if "ber_curve_csv" in metrics:
        print(f"BER curve CSV       : {metrics['ber_curve_csv']}")
        print(f"BER curve plot      : {metrics['ber_curve_plot']}")
    print(f"Artifacts directory : {metrics['artifacts_dir']}")


if __name__ == "__main__":
    main()
