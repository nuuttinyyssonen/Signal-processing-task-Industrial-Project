import numpy as np

from downsample import min_max_downsample


def test_min_max_downsample_returns_original_rows_in_time_order():
    signal = np.array([
        [5, 10],
        [1, 8],
        [7, 2],
        [4, 9],
        [3, 6],
    ], dtype=np.uint16)

    downsampled, indices = min_max_downsample(signal, factor=4)

    expected_indices = np.array([0, 1, 2, 4])
    assert np.array_equal(indices, expected_indices)
    assert np.array_equal(downsampled, signal[expected_indices])