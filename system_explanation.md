# Communication System Pipeline Explanation

This document details the overall flow, individual processing blocks, and configurable variables within the End-to-End Communication System project.

---

## 1. Overall Flow of the Project

The system simulates a complete digital communication link from transmission to reception:
1. **Analog Source Generation:** Creates a continuous-time analog signal (the information).
2. **Analog-to-Digital Conversion (ADC):** The signal is sampled in time and quantized in amplitude, then converted to a binary stream (PCM words).
3. **Line Coding:** Binary bits are mapped to discrete voltage levels based on a chosen coding scheme.
4. **Pulse Shaping:** Discrete voltage levels are converted into continuous transmission waveforms to limit bandwidth.
5. **Channel:** The waveform passes through an imperfect channel where attenuation and Additive White Gaussian Noise (AWGN) are introduced.
6. **Receiver & Matched Filter:** The noisy received waveform is filtered to maximize the Signal-to-Noise Ratio at the sampling instants.
7. **Decision & Decoding:** The filtered waveform is sampled, and thresholds are applied to decide if a 0 or 1 was transmitted.
8. **Performance Evaluation:** The recovered bits are compared against the original bitstream to calculate the Bit Error Rate (BER).

---

## 2. Detailed Block Explanations

### Block 1: Source Signal (`set_source_signal`)
* **What it does:** Generates the original continuous-time analog message signal.
* **How it does it:** Computes mathematical waveforms (e.g., sine, cosine, multi-tone) over a defined duration and frequency.
* **Output:** `analog_time` (time array) and `analog_signal` (continuous amplitude values).
* **Handled by next block:** Passed directly to the Sampling block to be discretized in time.

### Block 2: Sampling (`set_sampling`)
* **What it does:** Converts the continuous-time signal into a discrete-time sequence.
* **How it does it:** Extracts amplitude values at regular intervals defined by the `sampling_rate_hz`.
* **Output:** `sampled_signal` (an array of discrete signal values).
* **Handled by next block:** Passed to the Quantization block to discretize the amplitudes.

### Block 3: Quantization & PCM (`set_quantization`)
* **What it does:** Approximates the continuous amplitude values into a fixed set of discrete levels and encodes them into binary Pulse Code Modulation (PCM) words.
* **How it does it:** Divides the voltage range between `min_value` and `max_value` into distinct levels based on `bits_per_sample`. It assigns each sample to the nearest level and generates a binary string.
* **Output:** `quantized_signal`, `pcm_words` (binary representation), and an aggregated `bitstream`.
* **Handled by next block:** The binary `bitstream` is sent to the Line Coding block for modulation.

### Block 4: Line Coding (`set_line_coding`)
* **What it does:** Maps binary bits (1s and 0s) to discrete voltage levels suitable for transmission.
* **How it does it:** Uses rules based on the chosen scheme. For example, Polar maps 1 to +V and 0 to -V; On-Off maps 1 to +V and 0 to 0V; Bipolar alternates the polarity of 1s (+V, -V) and maps 0 to 0V.
* **Output:** `line_symbols` (an array of discrete voltages).
* **Handled by next block:** Passed to Pulse Shaping to turn these discrete impulses into a continuous waveform.

### Block 5: Pulse Shaping (`set_pulse_shaping`)
* **What it does:** Smooths the discrete line symbols into a continuous waveform to fit within a specific bandwidth.
* **How it does it:** Convolves the discrete symbols with a shaping filter (like Raised Cosine, NRZ, RZ, or Sinc).
* **Output:** `transmit_waveform` (the continuous signal ready for transmission).
* **Handled by next block:** Sent into the physical Channel model.

### Block 6: Channel (`set_channel`)
* **What it does:** Simulates real-world transmission impairments.
* **How it does it:** Multiplies the signal by an `attenuation` factor and adds random Additive White Gaussian Noise (AWGN). The noise level is dictated by `noise_std` or calculated from `snr_db`.
* **Output:** `received_waveform` (the degraded signal) and `noise` (the isolated noise array).
* **Handled by next block:** Picked up by the Receiver block for processing.

### Block 7: Receiver & Matched Filter (`set_receiver`)
* **What it does:** Filters out noise and decides which binary bits were sent.
* **How it does it:** Passes the `received_waveform` through a Matched Filter (identical to the transmission pulse shape reversed) to maximize the SNR. It then samples the peaks of this filtered waveform and compares them against a mathematical `decision_threshold`.
* **Output:** `recovered_bits` (the final binary sequence determined by the receiver).
* **Handled by next block:** Compared against the original `bitstream` to calculate the overall system Bit Error Rate (BER).

---

## 3. Configuration Variables Table

Here is a comprehensive table of variables you can manipulate in `simulation_template.py` to change the behavior of the system.

| Function Block | Variable Name | Description | Example / Possible Values |
| :--- | :--- | :--- | :--- |
| **`build_my_simulation`** | `scheme` | The line coding scheme | `"on_off"`, `"polar"`, `"bipolar"` |
| | `pulse` | The pulse shaping filter | `"nrz"`, `"rz"`, `"raised_cosine"`, `"sinc"` |
| | `noise_std` | Direct control of AWGN standard deviation. Overrides SNR if not `None`. | `0.1`, `5.0`, `None` |
| **`set_source_signal`** | `waveform` | Shape of the analog message | `"cosine"`, `"sine"`, `"square"`, `"multi_tone"` |
| | `amplitude` | Peak amplitude of the primary wave | `1.0`, `2.5`, etc. |
| | `frequency_hz` | Frequency of the primary wave | `5.0`, `10.0` |
| | `secondary_amplitude` | Amplitude of secondary wave (if multi-tone) | `0.35`, `0.0` |
| | `secondary_frequency_hz`| Frequency of secondary wave (if multi-tone)| `13.0`, `0.0` |
| | `duration_s` | Length of the simulation in seconds | `1.0`, `5.0` |
| **`set_sampling`** | `sampling_rate_hz` | How many samples are taken per second | `40.0`, `80.0`, `100.0` |
| **`set_quantization`**| `bits_per_sample` | Resolution of the ADC | `4`, `8`, `16` |
| | `min_value` / `max_value`| The clipping boundaries of the quantizer | `-1.5` / `1.5` |
| **`set_line_coding`** | `one_level` | The voltage amplitude for a logical "1" | `1.0`, `5.0` |
| **`set_pulse_shaping`**| `samples_per_symbol`| The digital oversampling rate for the analog waveform | `16`, `32`, `64` |
| | `rolloff` | The bandwidth excess factor (only for Raised Cosine) | `0.0` to `1.0` (e.g., `0.35`) |
| | `span_symbols` | The length of the pulse filter in symbols | `4`, `6`, `8` |
| **`set_channel`** | `noise_enabled` | Toggle AWGN on or off | `True`, `False` |
| | `snr_db` | Signal-to-Noise ratio (ignored if `noise_std` is set) | `10.0`, `18.0` |
| | `attenuation` | Signal scaling factor (e.g. signal fading) | `1.0` (no fading), `0.5` |
| | `random_seed` | Seed for repeatable noise generation | `7`, `42` |
| **`set_receiver`** | `sample_offset` | Manual shift for the optimal sampling instant | `0`, `1`, `-1` |
| **`set_output`** | `run_name` | The base name for the output folder | `"assignment_demo"` |
| | `save_plots` | Saves images of waveforms and eye diagrams | `True`, `False` |
| **`set_ber_waterfall`**| `enabled` | Iterates SNR to plot BER vs SNR | `True`, `False` |
| | `snr_db_values` | The X-axis points for the waterfall curve | `[-4, 0, 4, 8, 12]` |
| | `min_bit_count` | The number of bits transmitted to test BER accuracy | `100_000`, `1_000_000` |
