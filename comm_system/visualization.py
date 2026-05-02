from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from .config import OutputConfig, PulseShapeConfig
from .pulse_shaping import build_pulse


def render_all_figures(
    output_dir: Path,
    output_config: OutputConfig,
    analog_time: np.ndarray,
    analog_signal: np.ndarray,
    sample_time: np.ndarray,
    sampled_signal: np.ndarray,
    quantized_signal: np.ndarray,
    bitstream: np.ndarray,
    line_symbols: np.ndarray,
    transmit_waveform: np.ndarray,
    received_waveform: np.ndarray,
    matched_waveform: np.ndarray,
    pulse_config: PulseShapeConfig,
) -> None:
    if not output_config.save_plots and not output_config.show_plots:
        return

    _apply_plot_backend(output_config)

    figures: list[tuple[str, plt.Figure]] = [
        (
            "01_source_sampling_quantization",
            _plot_source_and_quantization(
                analog_time,
                analog_signal,
                sample_time,
                sampled_signal,
                quantized_signal,
            ),
        ),
        ("02_bitstream_preview", _plot_bitstream(bitstream, output_config)),
        ("03_line_symbols", _plot_symbol_levels(line_symbols)),
        (
            "04_tx_rx_waveforms",
            _plot_waveforms(transmit_waveform, received_waveform, matched_waveform),
        ),
        (
            "05_eye_tx",
            _plot_eye_diagram(
                transmit_waveform,
                pulse_config,
                output_config,
                "Eye Diagram - Transmit Waveform",
            ),
        ),
        (
            "06_eye_rx",
            _plot_eye_diagram(
                received_waveform,
                pulse_config,
                output_config,
                "Eye Diagram - Received Waveform",
            ),
        ),
        (
            "07_eye_matched",
            _plot_eye_diagram(
                matched_waveform,
                pulse_config,
                output_config,
                "Eye Diagram - Matched Filter Output",
            ),
        ),
        ("08_pulse_time_domain", _plot_pulse_shape(pulse_config)),
        ("09_pulse_frequency_domain", _plot_pulse_spectrum_comparison(pulse_config)),
    ]

    if output_config.save_plots:
        for stem, figure in figures:
            figure.savefig(output_dir / f"{stem}.png", dpi=output_config.figure_dpi)

    if output_config.show_plots:
        plt.show()

    if output_config.close_after_show or not output_config.show_plots:
        plt.close("all")


def _apply_plot_backend(output_config: OutputConfig) -> None:
    backend = output_config.plot_backend.lower()
    if backend == "matplotlib":
        plt.style.use(output_config.plot_style)
        return

    if backend == "seaborn":
        import seaborn as sns

        style = output_config.plot_style
        if style == "default":
            style = "darkgrid"
        sns.set_theme(
            style=style,
            context=output_config.seaborn_context,
            palette=output_config.seaborn_palette,
        )
        return

    raise ValueError(f"Unsupported plot backend: {output_config.plot_backend}")


def _plot_source_and_quantization(
    analog_time: np.ndarray,
    analog_signal: np.ndarray,
    sample_time: np.ndarray,
    sampled_signal: np.ndarray,
    quantized_signal: np.ndarray,
) -> plt.Figure:
    fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=False)

    axes[0].plot(analog_time, analog_signal, color="tab:blue")
    axes[0].set_title("Analog Source Signal")
    axes[0].set_xlabel("Time (s)")
    axes[0].set_ylabel("Amplitude")
    axes[0].grid(True, alpha=0.25)

    axes[1].plot(analog_time, analog_signal, color="lightgray", linewidth=1.0)
    axes[1].stem(sample_time, sampled_signal, linefmt="tab:orange", markerfmt="o", basefmt=" ")
    axes[1].set_title("Sampled Signal")
    axes[1].set_xlabel("Time (s)")
    axes[1].set_ylabel("Amplitude")
    axes[1].grid(True, alpha=0.25)

    axes[2].step(sample_time, quantized_signal, where="mid", color="tab:green")
    axes[2].plot(sample_time, sampled_signal, "o", color="tab:red", markersize=4)
    axes[2].set_title("Quantized Samples")
    axes[2].set_xlabel("Time (s)")
    axes[2].set_ylabel("Amplitude")
    axes[2].grid(True, alpha=0.25)

    fig.tight_layout()
    return fig


def _plot_bitstream(bitstream: np.ndarray, output_config: OutputConfig) -> plt.Figure:
    preview = bitstream[: output_config.bitstream_preview_bits]
    fig, ax = plt.subplots(figsize=(12, 3))
    ax.step(np.arange(len(preview)), preview, where="post", color="tab:purple")
    ax.set_title(f"Bitstream Preview ({len(preview)} bits)")
    ax.set_xlabel("Bit Index")
    ax.set_ylabel("Bit")
    ax.set_ylim(-0.2, 1.2)
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    return fig


def _plot_symbol_levels(symbols: np.ndarray) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(12, 3))
    ax.step(np.arange(len(symbols)), symbols, where="post", color="tab:brown")
    ax.set_title("Line-Coded Symbol Levels")
    ax.set_xlabel("Symbol Index")
    ax.set_ylabel("Level")
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    return fig


def _plot_waveforms(
    transmit_waveform: np.ndarray,
    received_waveform: np.ndarray,
    matched_waveform: np.ndarray,
) -> plt.Figure:
    fig, axes = plt.subplots(3, 1, figsize=(12, 9), sharex=False)

    axes[0].plot(transmit_waveform, color="tab:blue")
    axes[0].set_title("Transmit Waveform After Pulse Shaping")
    axes[0].set_ylabel("Amplitude")
    axes[0].grid(True, alpha=0.25)

    axes[1].plot(received_waveform, color="tab:red")
    axes[1].set_title("Received Waveform After Channel")
    axes[1].set_ylabel("Amplitude")
    axes[1].grid(True, alpha=0.25)

    axes[2].plot(matched_waveform, color="tab:green")
    axes[2].set_title("Matched Filter Output")
    axes[2].set_xlabel("Sample Index")
    axes[2].set_ylabel("Amplitude")
    axes[2].grid(True, alpha=0.25)

    fig.tight_layout()
    return fig


def _plot_eye_diagram(
    waveform: np.ndarray,
    pulse_config: PulseShapeConfig,
    output_config: OutputConfig,
    title: str,
) -> plt.Figure:
    span = pulse_config.samples_per_symbol * output_config.eye_symbols
    traces = _eye_segments(waveform, span, output_config.eye_trace_count)

    fig, ax = plt.subplots(figsize=(10, 5))
    for trace in traces:
        ax.plot(trace, color="tab:blue", alpha=0.18)
    ax.set_title(title)
    ax.set_xlabel("Sample Index")
    ax.set_ylabel("Amplitude")
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    return fig


def _plot_pulse_shape(pulse_config: PulseShapeConfig) -> plt.Figure:
    pulse = build_pulse(pulse_config)
    samples_per_symbol = pulse_config.samples_per_symbol
    symbol_time = np.arange(len(pulse), dtype=float) / samples_per_symbol
    symbol_time -= symbol_time[len(symbol_time) // 2] if len(pulse) > samples_per_symbol else 0.0

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(symbol_time, pulse, color="tab:blue")
    ax.set_title(f"Pulse Shape - {pulse_config.pulse}")
    ax.set_xlabel("Time (symbol periods)")
    ax.set_ylabel("Amplitude")
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    return fig


def _plot_pulse_spectrum_comparison(pulse_config: PulseShapeConfig) -> plt.Figure:
    rc_config = _copy_pulse_config(pulse_config, "raised_cosine")
    sinc_config = _copy_pulse_config(pulse_config, "sinc")
    selected_config = _copy_pulse_config(pulse_config, pulse_config.pulse)

    curves = [
        (f"Selected: {pulse_config.pulse}", build_pulse(selected_config)),
        ("Raised Cosine", build_pulse(rc_config)),
        ("Sinc", build_pulse(sinc_config)),
    ]

    fig, ax = plt.subplots(figsize=(10, 5))
    for label, pulse in curves:
        frequency, magnitude_db = _pulse_spectrum_db(pulse, pulse_config.samples_per_symbol)
        ax.plot(frequency, magnitude_db, label=label)

    ax.set_title("Pulse Frequency-Domain Comparison")
    ax.set_xlabel("Frequency / Symbol Rate")
    ax.set_ylabel("Magnitude (dB, normalized)")
    ax.set_xlim(-2.5, 2.5)
    ax.set_ylim(-80, 5)
    ax.grid(True, alpha=0.25)
    ax.legend()
    fig.tight_layout()
    return fig


def plot_ber_curve(
    snr_db_values: np.ndarray,
    ber_values: np.ndarray,
    title: str = "BER vs SNR Waterfall Curve",
) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(9, 5))
    clipped_ber = np.maximum(ber_values, 1e-7)
    ax.semilogy(snr_db_values, clipped_ber, marker="o", color="tab:red")
    ax.set_title(title)
    ax.set_xlabel("SNR (dB)")
    ax.set_ylabel("Bit Error Rate")
    ax.grid(True, which="both", alpha=0.25)
    fig.tight_layout()
    return fig


def save_ber_curve_plot(
    output_dir: Path,
    output_config: OutputConfig,
    snr_db_values: np.ndarray,
    ber_values: np.ndarray,
) -> None:
    if not output_config.save_plots and not output_config.show_plots:
        return

    _apply_plot_backend(output_config)
    figure = plot_ber_curve(snr_db_values, ber_values)
    if output_config.save_plots:
        figure.savefig(output_dir / "10_ber_vs_snr_waterfall.png", dpi=output_config.figure_dpi)
    if output_config.show_plots:
        plt.show()
    if output_config.close_after_show or not output_config.show_plots:
        plt.close(figure)


def _eye_segments(waveform: np.ndarray, span: int, max_traces: int) -> list[np.ndarray]:
    if len(waveform) < span or span <= 0:
        return []

    segments = []
    step = max(1, span // 2)
    for start in range(0, len(waveform) - span, step):
        segments.append(waveform[start : start + span])
        if len(segments) >= max_traces:
            break
    return segments


def _copy_pulse_config(config: PulseShapeConfig, pulse: str) -> PulseShapeConfig:
    return PulseShapeConfig(
        pulse=pulse,
        samples_per_symbol=config.samples_per_symbol,
        amplitude=config.amplitude,
        rolloff=config.rolloff,
        span_symbols=config.span_symbols,
        rz_duty_cycle=config.rz_duty_cycle,
    )


def _pulse_spectrum_db(pulse: np.ndarray, samples_per_symbol: int) -> tuple[np.ndarray, np.ndarray]:
    fft_size = max(4096, 2 ** int(np.ceil(np.log2(len(pulse) * 16))))
    spectrum = np.fft.fftshift(np.fft.fft(pulse, n=fft_size))
    frequency = np.fft.fftshift(np.fft.fftfreq(fft_size, d=1.0 / samples_per_symbol))
    magnitude = np.abs(spectrum)
    magnitude = magnitude / max(np.max(magnitude), 1e-12)
    magnitude_db = 20.0 * np.log10(np.maximum(magnitude, 1e-12))
    return frequency, magnitude_db
