import numpy as np

from baseline import remove_baseline, remove_baseline_fast


def test_fast_baseline_tracks_slow_drift_with_close_to_rolling_median():
    sample_rate = 50_000
    samples = np.arange(250_000)
    rng = np.random.default_rng(42)
    signal = (
        30_000
        + 2_000 * np.sin(2 * np.pi * samples / 500_000)
        + rng.normal(0, 200, samples.size)
    )
    signal[100_000] += 5_000

    _, exact_baseline = remove_baseline(signal, sample_rate)
    processed, fast_baseline = remove_baseline_fast(signal, sample_rate)

    assert processed.shape == signal.shape
    assert np.all(np.isfinite(processed))
    assert np.mean(np.abs(fast_baseline - exact_baseline)) < 30
    assert abs(fast_baseline[100_000] - exact_baseline[100_000]) < 30
