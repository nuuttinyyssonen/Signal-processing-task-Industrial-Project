import threading

import numpy as np

from components.plots import PlotsPanel


def test_raw_overview_keeps_minimum_and_maximum_per_bucket():
    signal = np.array([4, 1, 7, 3, 5, 2, 9, 6], dtype=np.uint16)

    indices, values = PlotsPanel._compute_overview_data(
        signal,
        sample_count=len(signal),
        sample_rate=10,
        bucket_count=2,
        remove_baseline=False,
        smoothing=False,
    )

    assert np.array_equal(indices, [1, 2, 5, 6])
    assert np.array_equal(values, signal[indices])


def test_overview_computation_stops_when_cancelled():
    cancellation = threading.Event()
    cancellation.set()

    result = PlotsPanel._compute_overview_data(
        np.arange(100, dtype=np.uint16),
        sample_count=100,
        sample_rate=10,
        bucket_count=5,
        remove_baseline=False,
        smoothing=False,
        cancel_event=cancellation,
    )

    assert result is None


def test_processed_overview_preserves_bucket_extrema():
    signal = np.array([1, 7, 3, 9, 4, 8, 2, 6], dtype=np.float64)
    window = int(0.3 * 10)
    baseline = np.array([
        np.median(signal[max(0, index - window // 2):
                         min(len(signal), index + window // 2 + 1)])
        for index in range(len(signal))
    ])
    processed = signal - baseline
    expected_indices = np.array([2, 3, 4, 5])
    expected_values = processed[expected_indices]

    indices, values = PlotsPanel._compute_overview_data(
        signal,
        sample_count=len(signal),
        sample_rate=10,
        bucket_count=2,
        remove_baseline=True,
        smoothing=False,
    )

    assert np.array_equal(indices, expected_indices)
    assert np.array_equal(values, expected_values)
