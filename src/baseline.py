import numpy as np
import pandas as pd


def remove_baseline(signal, fs, window_s=0.3):
    "Remove baseline using a rolling median"

    x = signal.astype(np.float64)
    window = int(window_s * fs)

    baseline = (
        pd.Series(x)
        .rolling(window, center=True, min_periods=1)
        .median()
        .to_numpy()
    )

    return x - baseline, baseline


def remove_baseline_fast(signal, fs, window_s=0.3, max_stride=20):
    """Approximate the rolling-median baseline on a reduced-rate signal."""
    x = np.asarray(signal, dtype=np.float64)
    if x.ndim != 1:
        raise ValueError("signal must be one-dimensional")
    if fs <= 0 or window_s <= 0 or max_stride <= 0:
        raise ValueError("fs, window_s, and max_stride must be positive")
    if x.size == 0:
        return x.copy(), x.copy()

    window_samples = max(1, int(window_s * fs))
    stride = min(max_stride, max(1, window_samples // 100))
    full_samples = x.size - x.size % stride
    block_means = x[:full_samples].reshape(-1, stride).mean(axis=1)
    centers = (
        np.arange(block_means.size, dtype=np.float64) * stride
        + (stride - 1) / 2
    )
    if full_samples < x.size:
        block_means = np.append(block_means, x[full_samples:].mean())
        centers = np.append(centers, (full_samples + x.size - 1) / 2)

    reduced_window = max(1, int(round(window_samples / stride)))
    sampled_baseline = (
        pd.Series(block_means)
        .rolling(reduced_window, center=True, min_periods=1)
        .median()
        .to_numpy()
    )
    baseline = np.interp(np.arange(x.size), centers, sampled_baseline)
    return x - baseline, baseline