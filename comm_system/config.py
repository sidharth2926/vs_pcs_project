from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class SourceConfig:
    waveform: str = "multi_tone"
    amplitude: float = 1.0
    frequency_hz: float = 5.0
    phase_rad: float = 0.0
    secondary_amplitude: float = 0.35
    secondary_frequency_hz: float = 13.0
    secondary_phase_rad: float = 0.0
    dc_offset: float = 0.0
    duration_s: float = 1.0
    analog_sample_rate_hz: float | None = None
    analog_oversample_factor: int = 40


@dataclass
class SamplingConfig:
    sampling_rate_hz: float = 80.0
    sample_phase_s: float = 0.0


@dataclass
class QuantizerConfig:
    bits_per_sample: int | None = 4
    quantization_levels: int | None = None
    min_value: float = -1.5
    max_value: float = 1.5


@dataclass
class LineCodeConfig:
    scheme: str = "polar"
    one_level: float = 1.0
    zero_level: float = 0.0
    bipolar_zero_level: float = 0.0
    bipolar_first_mark_positive: bool = True


@dataclass
class PulseShapeConfig:
    pulse: str = "nrz"
    samples_per_symbol: int = 32
    amplitude: float = 1.0
    rolloff: float = 0.35
    span_symbols: int = 6
    rz_duty_cycle: float = 0.5


@dataclass
class ChannelConfig:
    noise_enabled: bool = True
    snr_db: float = 18.0
    noise_std: float | None = None
    attenuation: float = 1.0
    dc_offset: float = 0.0
    random_seed: int = 7


@dataclass
class ReceiverConfig:
    decision_threshold: float = 0.0
    sample_offset: int = 0
    normalize_threshold_to_pulse_energy: bool = True
    bipolar_use_absolute_value: bool = True


@dataclass
class OutputConfig:
    root_dir: Path = field(default_factory=lambda: Path("artifacts"))
    run_name: str | None = None
    resolved_run_name: str | None = None
    save_plots: bool = False
    save_text: bool = True
    show_plots: bool = True
    plot_backend: str = "matplotlib"
    plot_style: str = "default"
    seaborn_context: str = "notebook"
    seaborn_palette: str = "deep"
    figure_dpi: int = 160
    eye_symbols: int = 2
    eye_trace_count: int = 120
    bitstream_preview_bits: int = 128
    close_after_show: bool = False


@dataclass
class BerCurveConfig:
    enabled: bool = False
    snr_db_values: list[float] = field(default_factory=lambda: [-8, -6, -4, -2, 0, 2, 4, 6, 8, 10, 12])
    min_bit_count: int = 100_000
    random_seed: int = 99
    bit_source: str = "random"


@dataclass
class SimulationConfig:
    source: SourceConfig = field(default_factory=SourceConfig)
    sampling: SamplingConfig = field(default_factory=SamplingConfig)
    quantizer: QuantizerConfig = field(default_factory=QuantizerConfig)
    line_code: LineCodeConfig = field(default_factory=LineCodeConfig)
    pulse_shape: PulseShapeConfig = field(default_factory=PulseShapeConfig)
    channel: ChannelConfig = field(default_factory=ChannelConfig)
    receiver: ReceiverConfig = field(default_factory=ReceiverConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    ber_curve: BerCurveConfig = field(default_factory=BerCurveConfig)


def build_config(scheme: str = "polar") -> SimulationConfig:
    scheme = scheme.lower()
    config = SimulationConfig()
    config.line_code.scheme = scheme

    if scheme == "on_off":
        config.line_code.one_level = 1.0
        config.line_code.zero_level = 0.0
        config.receiver.decision_threshold = 0.5
    elif scheme == "polar":
        config.line_code.one_level = 1.0
        config.line_code.zero_level = -1.0
        config.receiver.decision_threshold = 0.0
    elif scheme == "bipolar":
        config.line_code.one_level = 1.0
        config.line_code.zero_level = 0.0
        config.line_code.bipolar_zero_level = 0.0
        config.receiver.decision_threshold = 0.5
    else:
        raise ValueError(f"Unsupported signalling scheme: {scheme}")

    return config
