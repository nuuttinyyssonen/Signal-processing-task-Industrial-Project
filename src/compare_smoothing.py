import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import matplotlib.pyplot as plt
import numpy as np

from check import get_samples_in_range
from smooth import smooth_gaussian

ROOT = Path(__file__).resolve().parents[1]
SIGNAL = ROOT / "data" / "example_out" / "signal.u16"
META = json.loads(SIGNAL.with_name("meta.json").read_text(encoding="utf-8"))
FS = META["sample_rate"]
CHANNELS = META["channels"]

START_S = 133.2
DURATION_S = 0.05
QUIET_START_S = 2.0
QUIET_DURATION_S = 1.0
GAUSS_SIGMA_S = 2 / FS       # 2 samples: 40 us at 50 kHz


def smoothing_versions(signal):
    return {
        "raw": signal,
        "gaussian": smooth_gaussian(signal, GAUSS_SIGMA_S, FS),
    }


def measure_spread(signal):
    standard_deviation = np.std(signal)
    median = np.median(signal)
    robust_spread = 1.4826 * np.median(np.abs(signal - median))
    return standard_deviation, robust_spread


samples = get_samples_in_range(SIGNAL, START_S, START_S + DURATION_S)
times = START_S + np.arange(len(samples)) / FS

fig, axes = plt.subplots(len(CHANNELS), 1, figsize=(11, 7), sharex=True)
for channel_index, (axis, channel_name) in enumerate(zip(axes, CHANNELS)):
    raw = samples[:, channel_index].astype(np.float32)
    versions = smoothing_versions(raw)
    axis.plot(times, versions["raw"], color="gray", alpha=0.55, label="raw")
    axis.plot(times, versions["gaussian"], label="Gaussian (2-sample sigma)")
    axis.set_ylabel(channel_name)
    axis.legend()

axes[-1].set_xlabel("time (s)")
fig.suptitle(f"Smoothing comparison, {START_S:g}-{START_S + DURATION_S:g} s")
plt.tight_layout()

quiet_samples = get_samples_in_range(
    SIGNAL,
    QUIET_START_S,
    QUIET_START_S + QUIET_DURATION_S,
).astype(np.float32)
print(
    f"Quiet interval: {QUIET_START_S:g}-{QUIET_START_S + QUIET_DURATION_S:g} s "
    "(standard deviation and scaled MAD; no detrending)"
)
print(f"{'channel':<8} {'method':<10} {'std':>8} {'MAD spread':>11} {'std change':>12} {'MAD change':>12}")
for channel_index, channel_name in enumerate(CHANNELS):
    versions = smoothing_versions(quiet_samples[:, channel_index])
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