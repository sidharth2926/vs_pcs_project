from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re

import numpy as np

from .channel import add_awgn
from .config import ChannelConfig, SimulationConfig
from .io_utils import dataclass_to_dict, dump_json, ensure_directory, save_array_text, save_text_lines
from .line_coding import encode_line
from .pcm import build_bitstream, quantize_samples, resolve_quantizer_settings
from .pulse_shaping import build_pulse, shape_symbols
from .receiver import bit_error_rate, decide_bits, matched_filter_receive
from .source import generate_analog_signal, sample_signal
from .visualization import render_all_figures, save_ber_curve_plot


def run_simulation(config: SimulationConfig) -> dict[str, float | int | str]:
    output_dir = _resolve_output_dir(config)
    quantizer_levels, quantizer_bits = resolve_quantizer_settings(config.quantizer)

    analog_time, analog_signal = generate_analog_signal(config.source)
    sample_time, sampled_signal = sample_signal(analog_time, analog_signal, config.sampling)
    quantized_signal, quantizer_indices, pcm_words = quantize_samples(sampled_signal, config.quantizer)
    bitstream = build_bitstream(pcm_words)

    line_symbols = encode_line(bitstream, config.line_code)
    pulse = build_pulse(config.pulse_shape)
    _, transmit_waveform = shape_symbols(
        line_symbols,
        pulse,
        config.pulse_shape.samples_per_symbol,
    )
    received_waveform, noise = add_awgn(transmit_waveform, config.channel)

    matched_waveform, symbol_samples = matched_filter_receive(
        received_waveform,
        pulse,
        config.pulse_shape,
        config.receiver,
    )
    recovered_bits = decide_bits(
        symbol_samples[: len(bitstream)],
        config.line_code,
        config.receiver,
        pulse_energy=float(np.sum(pulse**2)),
    )
    ber = bit_error_rate(bitstream, recovered_bits)

    metrics = {
        "scheme": config.line_code.scheme,
        "pulse": config.pulse_shape.pulse,
        "run_name": config.output.run_name or "",
        "sample_count": int(len(sampled_signal)),
        "bits_per_sample": int(quantizer_bits),
        "quantization_levels": int(quantizer_levels),
        "bitstream_length": int(len(bitstream)),
        "symbol_count": int(len(line_symbols)),
        "samples_per_symbol": int(config.pulse_shape.samples_per_symbol),
        "snr_db": float(config.channel.snr_db),
        "ber": float(ber),
        "artifacts_dir": str(output_dir),
    }

    if config.output.save_text:
        _write_text_artifacts(
            output_dir=output_dir,
            sample_time=sample_time,
            sampled_signal=sampled_signal,
            quantized_signal=quantized_signal,
            quantizer_indices=quantizer_indices,
            pcm_words=pcm_words,
            bitstream=bitstream,
            recovered_bits=recovered_bits,
            line_symbols=line_symbols,
            pulse=pulse,
            noise=noise,
            metrics=metrics,
            config=config,
        )

    if config.ber_curve.enabled:
        ber_curve_metrics = run_ber_curve(config, base_bitstream=bitstream)
        metrics["ber_curve_csv"] = str(output_dir / "ber_vs_snr.csv")
        metrics["ber_curve_plot"] = str(output_dir / "10_ber_vs_snr_waterfall.png")
        metrics["ber_curve_min_ber"] = float(np.min(ber_curve_metrics["ber_values"]))

    render_all_figures(
        output_dir=output_dir,
        output_config=config.output,
        analog_time=analog_time,
        analog_signal=analog_signal,
        sample_time=sample_time,
        sampled_signal=sampled_signal,
        quantized_signal=quantized_signal,
        bitstream=bitstream,
        line_symbols=line_symbols,
        transmit_waveform=transmit_waveform,
        received_waveform=received_waveform,
        matched_waveform=matched_waveform,
        pulse_config=config.pulse_shape,
    )

    return metrics


def run_ber_curve(
    config: SimulationConfig,
    base_bitstream: np.ndarray | None = None,
) -> dict[str, np.ndarray]:
    output_dir = _resolve_output_dir(config)
    bitstream = _resolve_ber_curve_bits(config, base_bitstream)
    pulse = build_pulse(config.pulse_shape)

    rows = ["snr_db,bit_errors,total_bits,ber"]
    snr_values = np.array(config.ber_curve.snr_db_values, dtype=float)
    ber_values = np.zeros_like(snr_values, dtype=float)
    error_counts = np.zeros_like(snr_values, dtype=int)

    for index, snr_db in enumerate(snr_values):
        line_symbols = encode_line(bitstream, config.line_code)
        _, transmit_waveform = shape_symbols(
            line_symbols,
            pulse,
            config.pulse_shape.samples_per_symbol,
        )
        channel_config = _channel_for_ber_point(
            config.channel,
            float(snr_db),
            config.ber_curve.random_seed + index,
        )
        received_waveform, _ = add_awgn(transmit_waveform, channel_config)
        _, symbol_samples = matched_filter_receive(
            received_waveform,
            pulse,
            config.pulse_shape,
            config.receiver,
        )
        recovered_bits = decide_bits(
            symbol_samples[: len(bitstream)],
            config.line_code,
            config.receiver,
            pulse_energy=float(np.sum(pulse**2)),
        )

        limit = min(len(bitstream), len(recovered_bits))
        bit_errors = int(np.count_nonzero(bitstream[:limit] != recovered_bits[:limit]))
        ber = bit_errors / limit if limit else 0.0
        error_counts[index] = bit_errors
        ber_values[index] = ber
        rows.append(f"{snr_db:.6f},{bit_errors},{limit},{ber:.12g}")

    if config.output.save_text:
        save_text_lines(output_dir / "ber_vs_snr.csv", rows)
        dump_json(
            output_dir / "ber_vs_snr.json",
            {
                "snr_db_values": snr_values.tolist(),
                "ber_values": ber_values.tolist(),
                "bit_errors": error_counts.tolist(),
                "total_bits": int(len(bitstream)),
            },
        )

    save_ber_curve_plot(output_dir, config.output, snr_values, ber_values)

    return {
        "snr_db_values": snr_values,
        "ber_values": ber_values,
        "bit_errors": error_counts,
    }


def _write_text_artifacts(
    output_dir: Path,
    sample_time: np.ndarray,
    sampled_signal: np.ndarray,
    quantized_signal: np.ndarray,
    quantizer_indices: np.ndarray,
    pcm_words: np.ndarray,
    bitstream: np.ndarray,
    recovered_bits: np.ndarray,
    line_symbols: np.ndarray,
    pulse: np.ndarray,
    noise: np.ndarray,
    metrics: dict[str, float | int | str],
    config: SimulationConfig,
) -> None:
    sample_lines = [
        "sample_index,time_s,sampled_value,quantized_value,quantizer_index,pcm_word"
    ]
    for index, (time_s, sampled, quantized, qindex, word) in enumerate(
        zip(
            sample_time,
            sampled_signal,
            quantized_signal,
            quantizer_indices,
            pcm_words,
            strict=False,
        )
    ):
        sample_lines.append(
            f"{index},{time_s:.6f},{sampled:.6f},{quantized:.6f},{int(qindex)},{''.join(word)}"
        )

    save_text_lines(output_dir / "quantized_samples.csv", sample_lines)
    save_text_lines(
        output_dir / "quantized_words.txt",
        ["".join(word) for word in pcm_words],
    )
    save_text_lines(
        output_dir / "bitstream.txt",
        ["".join(bitstream.astype(str).tolist())],
    )
    save_text_lines(
        output_dir / "recovered_bitstream.txt",
        ["".join(recovered_bits.astype(str).tolist())],
    )
    save_array_text(output_dir / "line_symbols.txt", line_symbols)
    save_array_text(output_dir / "pulse_shape.txt", pulse)
    save_array_text(output_dir / "noise_samples.txt", noise)
    dump_json(output_dir / "metrics.json", metrics)
    dump_json(output_dir / "config_snapshot.json", dataclass_to_dict(config))


def _resolve_output_dir(config: SimulationConfig) -> Path:
    if not config.output.run_name:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        config.output.run_name = f"run_{timestamp}"

    run_name = _safe_path_part(config.output.run_name)
    scheme = _safe_path_part(config.line_code.scheme)
    pulse = _safe_path_part(config.pulse_shape.pulse)
    return ensure_directory(config.output.root_dir / run_name / scheme / pulse)


def _safe_path_part(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "_", value.strip().lower())
    return cleaned.strip("._") or "default"


def _resolve_ber_curve_bits(
    config: SimulationConfig,
    base_bitstream: np.ndarray | None,
) -> np.ndarray:
    bit_source = config.ber_curve.bit_source.lower()
    if bit_source == "random":
        generator = np.random.default_rng(config.ber_curve.random_seed)
        return generator.integers(0, 2, size=config.ber_curve.min_bit_count, dtype=int)

    if bit_source != "pcm_repeated":
        raise ValueError("ber_curve.bit_source must be 'random' or 'pcm_repeated'")

    if base_bitstream is None:
        analog_time, analog_signal = generate_analog_signal(config.source)
        sample_time, sampled_signal = sample_signal(analog_time, analog_signal, config.sampling)
        del sample_time
        _, _, pcm_words = quantize_samples(sampled_signal, config.quantizer)
        base_bitstream = build_bitstream(pcm_words)

    if len(base_bitstream) == 0:
        return base_bitstream

    repeat_count = int(np.ceil(config.ber_curve.min_bit_count / len(base_bitstream)))
    tiled = np.tile(base_bitstream, repeat_count)
    return tiled[: config.ber_curve.min_bit_count].astype(int)


def _channel_for_ber_point(
    base_config: ChannelConfig,
    snr_db: float,
    random_seed: int,
) -> ChannelConfig:
    return ChannelConfig(
        noise_enabled=True,
        snr_db=snr_db,
        noise_std=None,
        attenuation=base_config.attenuation,
        dc_offset=base_config.dc_offset,
        random_seed=random_seed,
    )
