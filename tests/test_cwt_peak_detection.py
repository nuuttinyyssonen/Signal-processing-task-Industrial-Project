from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from cwt_peak_detection import detect_peaks_cwt


DATA_PATH = Path(__file__).parents[1] / "data" / "example15peaks.csv"


def test_detect_peaks_cwt_finds_positive_and_negative_pulses_in_chunks(tmp_path):
    sample_rate = 1_000
    samples = np.arange(600)
    signal = np.full(samples.size, 100.0)
    signal += 50 * np.exp(-0.5 * ((samples - 180) / 10) ** 2)
    signal -= 30 * np.exp(-0.5 * ((samples - 420) / 10) ** 2)
    signal_path = tmp_path / "signal.f64"
    mapped_signal = np.memmap(
        signal_path,
        dtype=np.float64,
        mode="w+",
        shape=signal.shape,
    )
    mapped_signal[:] = signal
    mapped_signal.flush()

    peaks = detect_peaks_cwt(
        mapped_signal,
        sample_rate,
        widths=range(4, 17, 2),
        min_prominence=5,
        min_distance_s=0.1,
        min_height=5,
        polarity="both",
        chunk_size=200,
    )

    assert len(peaks) == 2
    assert abs(peaks[0].index - 180) <= 5
    assert peaks[0].polarity == "up"
    assert abs(peaks[1].index - 420) <= 5
    assert peaks[1].polarity == "down"


def test_example15peaks_cwt_reports_detected_peak_count():
    if not DATA_PATH.exists():
        pytest.skip("data/example15peaks.csv not found")

    signal = pd.read_csv(
        DATA_PATH,
        usecols=["adc2"],
        dtype=np.float64,
    ).to_numpy().ravel()
    peaks = detect_peaks_cwt(signal, sample_rate=50_000)
    smaller_chunks = detect_peaks_cwt(
        signal,
        sample_rate=50_000,
        chunk_size=250_000,
    )
    peak_regions = ((25, 60), (95, 150), (155, 212))
    zero_region = (220, 270)
    water_region = (280, 345)
    detections_by_region = [
        sum(start <= peak.time < stop for peak in peaks)
        for start, stop in peak_regions
    ]
    zero_detections = sum(
        zero_region[0] <= peak.time < zero_region[1] for peak in peaks
    )
    water_detections = sum(
        water_region[0] <= peak.time < water_region[1] for peak in peaks
    )

    print(
        f"example15peaks.csv: CWT detected {len(peaks)} peaks total; "
        f"{sum(detections_by_region)} real peaks "
        f"({detections_by_region}), {zero_detections} zero-amplitude "
        f"candidates and {water_detections} in the water-noise region"
    )
    assert detections_by_region == [15, 15, 15]
    assert len(smaller_chunks) == len(peaks)
    assert all(
        min(abs(peak.index - other.index) for other in smaller_chunks) <= 50
        for peak in peaks
    )
    assert all(
        min(abs(peak.index - other.index) for other in peaks) <= 50
        for peak in smaller_chunks
    )
    assert zero_detections <= 2
    assert water_detections <= 4
    assert 45 <= len(peaks) <= 50
