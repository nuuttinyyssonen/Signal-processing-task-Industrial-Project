import json

import numpy as np

from check import get_samples_in_range


# Test cases for get_samples_in_range function
def test_get_samples_in_range_returns_expected_slice(tmp_path):
    signal = np.arange(20 * 2, dtype=np.uint16).reshape(-1, 2)
    out_dir = tmp_path / "data"
    out_dir.mkdir()

    signal_path = out_dir / "signal.u16"
    signal.tofile(signal_path)

    meta = {"sample_rate": 10, "channels": ["adc1", "adc2"], "dtype": "uint16"}
    (out_dir / "meta.json").write_text(json.dumps(meta), encoding="utf-8")

    samples = get_samples_in_range(signal_path, 0.2, 0.5, sample_rate=10)

    expected = signal[2:5]
    assert np.array_equal(samples, expected)


def test_get_samples_in_range_clamps_to_signal_bounds(tmp_path):
    signal = np.arange(10 * 2, dtype=np.uint16).reshape(-1, 2)
    out_dir = tmp_path / "data"
    out_dir.mkdir()

    signal_path = out_dir / "signal.u16"
    signal.tofile(signal_path)

    meta = {"sample_rate": 10, "channels": ["adc1", "adc2"], "dtype": "uint16"}
    (out_dir / "meta.json").write_text(json.dumps(meta), encoding="utf-8")

    samples = get_samples_in_range(signal_path, -1.0, 999.0, sample_rate=10)

    assert samples.shape == signal.shape
    assert np.array_equal(samples, signal)
