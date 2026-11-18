import numpy as np
from peaks import detect_peaks, robust_noise

FS = 50_000

def make_noise(seed=0):
    rng = np.random.default_rng(seed)
    return rng.normal(0, 5, FS)

def test_robust_noise_ignores_single_outlier():
    assert np.isclose(robust_noise(np.array([-2, -1, 0, 1, 300])), 1.4826)

def test_finds_single_peak():
    signal = make_noise()
    signal[10_000] += 300

    idx, _, _ = detect_peaks(signal, FS)

    assert list(idx) == [10_000]

def test_noise_only_finds_nothing():
    signal = make_noise()
    idx, _, _ = detect_peaks(signal, FS)
    assert len(idx) == 0

def test_close_peaks_are_merged():
    signal = make_noise()
    signal[10_000] += 300
    signal[10_100] += 200
    idx, _, _ = detect_peaks(signal, FS)
    assert list(idx) == [10_000]

def test_far_peaks_are_both_found():
    signal = make_noise()
    signal[10_000] += 300
    signal[30_000] += 200
    idx, _, _ = detect_peaks(signal, FS)
    assert list(idx) == [10_000, 30_000]

def test_tiny_min_distance_does_not_crash():
    signal = make_noise()
    signal[10_000] += 300
    idx, _, _ = detect_peaks(signal, FS, min_distance_ms=0.01)
    assert list(idx) == [10_000]