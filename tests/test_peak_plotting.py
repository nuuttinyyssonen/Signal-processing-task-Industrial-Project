from types import SimpleNamespace

import numpy as np
from matplotlib.figure import Figure

from cwt_peak_detection import Peak
from components.plots import PlotsPanel


def test_peak_markers_are_drawn_on_overview_and_visible_detail():
    plot_state = SimpleNamespace(
        detected_peaks=[object(), object()],
        sample_rate=10,
        ax_overview=None,
    )
    plot_state._peak_display_values = lambda raw=False: (
        np.array([10, 20]),
        np.array([2.0, 4.0]),
    )
    overview, detail = Figure().subplots(2)
    plot_state.ax_overview = overview

    PlotsPanel._draw_peak_markers(plot_state, overview)
    PlotsPanel._draw_peak_markers(plot_state, detail, start=12, end=25)

    assert overview.collections[0].get_offsets().tolist() == [
        [1.0, 2.0],
        [2.0, 4.0],
    ]
    assert detail.collections[0].get_offsets().tolist() == [[2.0, 4.0]]


def test_peak_display_values_use_cached_detection_amplitude_for_processed_plot():
    signal = np.array([10, 20, 30], dtype=np.uint16)
    processed_chunks = []

    def process_chunk(*args):
        processed_chunks.append(args)
        return np.zeros(3)

    plot_state = SimpleNamespace(
        detected_peaks=[Peak(1, 0.1, 7.5, 5.0, "up")],
        signal_data=signal,
        remove_baseline_enabled=True,
        smoothing_enabled=True,
        _process_chunk=process_chunk,
    )

    indexes, values = PlotsPanel._peak_display_values(plot_state)
    raw_indexes, raw_values = PlotsPanel._peak_display_values(
        plot_state, raw=True
    )

    assert np.array_equal(indexes, [1])
    assert np.array_equal(values, [7.5])
    assert np.array_equal(raw_indexes, [1])
    assert np.array_equal(raw_values, [20])
    assert processed_chunks == []
