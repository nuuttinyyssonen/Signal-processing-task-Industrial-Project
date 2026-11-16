import threading

import numpy as np

from components.plots import PlotsPanel


def test_raw_overview_keeps_minimum_and_maximum_per_bucket():
    signal = np.array([4, 1, 7, 3, 5, 2, 9, 6], dtype=np.uint16)

    indices, values = PlotsPanel._compute_overview_data(
        signal,
        sample_count=len(signal),
        bucket_count=2,
    )

    assert np.array_equal(indices, [1, 2, 5, 6])
    assert np.array_equal(values, signal[indices])


def test_overview_computation_stops_when_cancelled():
    cancellation = threading.Event()
    cancellation.set()

    result = PlotsPanel._compute_overview_data(
        np.arange(100, dtype=np.uint16),
        sample_count=100,
        bucket_count=5,
        cancel_event=cancellation,
    )

    assert result is None
