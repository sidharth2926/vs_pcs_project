# End-to-End Digital Communication System

This project simulates a configurable digital communication chain:

1. Analog source generation
2. Sampling
3. Uniform quantization
4. PCM bitstream generation
5. Line coding (`on_off`, `polar`, `bipolar`)
6. Pulse shaping
7. AWGN channel
8. Matched filtering and symbol detection
9. Bit recovery and BER measurement
10. Figure and text artifact export

## Quick start

Install dependencies:

```powershell
pip install -r requirements.txt
```

Run a default simulation:

```powershell
python main.py
```

Run the assignment-ready controller template:

```powershell
python simulation_template.py
```

Generated artifacts are saved under `artifacts/<run_name>/<scheme>/<pulse>/`.

## What gets saved

- Quantized sample values
- Quantized PCM words
- Serialized bitstream
- Summary metrics in JSON
- Time-domain plots
- Eye diagrams at different stages

## Main tuning points

Edit `simulation_template.py` and use `build_my_simulation()` as the control panel for the whole chain.

- Source waveform, amplitude, frequency, phase, and duration
- Sampling rate and sample phase
- Quantizer levels or bits
- Line-code scheme and symbol amplitudes
- Pulse shape: `nrz`, `rz`, `raised_cosine`/`rc`, `sinc`, `half_sine`
- RC pulse rolloff, pulse span, RZ duty cycle, and samples per symbol
- Channel attenuation, SNR, fixed noise standard deviation, and seed
- Receiver threshold behavior and decision timing
- Plot backend and style using `matplotlib` or `seaborn`
- BER-vs-SNR waterfall curve settings
- BER test bits from `random` data or repeated PCM data using `pcm_repeated`
- Per-run artifact folder name using `set_output(..., run_name="assignment_demo")`

## Assignment demo artifacts

The controller template can generate the expected demo outputs:

- Sampling and quantization plot
- PCM bitstream text and preview plot
- Line-coded symbol output
- Eye diagram after pulse shaping
- Eye diagram after AWGN noise
- Matched filter output and matched-filter eye diagram
- Detected/recovered bits and BER
- RC and Sinc pulse frequency-domain comparison
- BER-vs-SNR waterfall curve

In `simulation_template.py`, use `set_output(config, save_plots=True, show_plots=False)` to save image files for slides.
Set `DEMO_MODE = "pulse_sweep"` in `simulation_template.py` to generate eye diagrams for all supported line-code and pulse combinations: `on_off`, `polar`, `bipolar` with `nrz`, `rz`, `raised_cosine`, and `sinc`.
