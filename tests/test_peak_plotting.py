from types import SimpleNamespace

import numpy as np
from matplotlib.figure import Figure

from components.plots import PlotsPanel


def test_peak_markers_are_drawn_on_overview_and_visible_detail():
    plot_state = SimpleNamespace(
        detected_peaks=[object(), object()],
        sample_rate=10,
    )
    plot_state._peak_display_values = lambda: (
        np.array([10, 20]),
        np.array([2.0, 4.0]),
    )
    overview, detail = Figure().subplots(2)

    PlotsPanel._draw_peak_markers(plot_state, overview)
    PlotsPanel._draw_peak_markers(plot_state, detail, start=12, end=25)

    assert overview.collections[0].get_offsets().tolist() == [
        [1.0, 2.0],
        [2.0, 4.0],
    ]
    assert detail.collections[0].get_offsets().tolist() == [[2.0, 4.0]]
