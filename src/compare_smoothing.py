import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import matplotlib.pyplot as plt
import numpy as np

from check import get_samples_in_range

ROOT = Path(__file__).resolve().parents[1]
SIGNAL = ROOT / "data" / "example_out" / "signal.u16"
SMOOTHED_SIGNAL = ROOT / "data" / "smoothed_out" / "signal.f32"
META = json.loads(SIGNAL.with_name("meta.json").read_text(encoding="utf-8"))
SMOOTHED_META_PATH = SMOOTHED_SIGNAL.with_name("meta.json")
if not SMOOTHED_SIGNAL.is_file() or not SMOOTHED_META_PATH.is_file():
    raise FileNotFoundError(
        "Smoothed output not found. Run src/smooth.py first to create data/smoothed_out."
    )
SMOOTHED_META = json.loads(SMOOTHED_META_PATH.read_text(encoding="utf-8"))
FS = META["sample_rate"]
CHANNELS = META["channels"]
if (
    SMOOTHED_META["sample_rate"] != FS
    or SMOOTHED_META["samples"] != META["samples"]
    or SMOOTHED_META["channels"] != CHANNELS
):
    raise ValueError("Smoothed output metadata does not match the raw signal")
SMOOTHING = SMOOTHED_META.get("smoothing", {})
if SMOOTHING.get("method") != "gaussian":
    raise ValueError("Expected Gaussian-smoothed output")

START_S = 133.2
DURATION_S = 0.05
QUIET_START_S = 2.0
QUIET_DURATION_S = 1.0


def measure_spread(signal):
    standard_deviation = np.std(signal)
    median = np.median(signal)
    robust_spread = 1.4826 * np.median(np.abs(signal - median))
    return standard_deviation, robust_spread


samples = get_samples_in_range(SIGNAL, START_S, START_S + DURATION_S)
smoothed_samples = get_samples_in_range(
    SMOOTHED_SIGNAL,
    START_S,
    START_S + DURATION_S,
)
if samples.shape != smoothed_samples.shape:
    raise ValueError("Raw and smoothed sample ranges have different shapes")
times = START_S + np.arange(len(samples)) / FS

fig, axes = plt.subplots(len(CHANNELS), 1, figsize=(11, 7), sharex=True)
for channel_index, (axis, channel_name) in enumerate(zip(axes, CHANNELS)):
    raw = samples[:, channel_index].astype(np.float32)
    smoothed = smoothed_samples[:, channel_index]
    axis.plot(times, raw, color="gray", alpha=0.55, label="raw")
    axis.plot(
        times,
        smoothed,
        label=f"Gaussian (sigma={SMOOTHING['sigma_s'] * 1000:g} ms)",
    )
    axis.set_ylabel(channel_name)
    axis.legend()

axes[-1].set_xlabel("time (s)")
fig.suptitle(f"Smoothing comparison, {START_S:g}-{START_S + DURATION_S:g} s")
plt.tight_layout()

quiet_raw = get_samples_in_range(
    SIGNAL,
    QUIET_START_S,
    QUIET_START_S + QUIET_DURATION_S,
).astype(np.float32)
quiet_smoothed = get_samples_in_range(
    SMOOTHED_SIGNAL,
    QUIET_START_S,
    QUIET_START_S + QUIET_DURATION_S,
)
if quiet_raw.shape != quiet_smoothed.shape:
    raise ValueError("Raw and smoothed quiet ranges have different shapes")
print(
    f"Quiet interval: {QUIET_START_S:g}-{QUIET_START_S + QUIET_DURATION_S:g} s "
    "(standard deviation and scaled MAD; no detrending)"
)
print(f"{'channel':<8} {'method':<10} {'std':>8} {'MAD spread':>11} {'std change':>12} {'MAD change':>12}")
for channel_index, channel_name in enumerate(CHANNELS):
    versions = {
        "raw": quiet_raw[:, channel_index],
        "gaussian": quiet_smoothed[:, channel_index],
    }
    raw_std, raw_mad = measure_spread(versions["raw"])
    for method, signal in versions.items():
        standard_deviation, robust_spread = measure_spread(signal)
        std_change = 100 * (standard_deviation / raw_std - 1) if raw_std else 0
        mad_change = 100 * (robust_spread / raw_mad - 1) if raw_mad else 0
        print(
            f"{channel_name:<8} {method:<10} {standard_deviation:8.3f} "
            f"{robust_spread:11.3f} {std_change:+11.1f}% {mad_change:+11.1f}%"
        )

plt.show()