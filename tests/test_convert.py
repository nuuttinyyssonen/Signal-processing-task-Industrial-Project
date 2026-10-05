from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from convert import convert_csv

CSV = Path(__file__).parents[1] / "data" / "example_signal.csv"

@pytest.fixture(scope="module")
def converted(tmp_path_factory):
    """Convert the original example file once and share the result between tests."""
    if not CSV.exists():
        pytest.skip("data/example_signal.csv not found")
    out = tmp_path_factory.mktemp("out")
    # 1M rows per chunk, so the file is read in several chunks and the last one is smaller
    meta = convert_csv(CSV, out, chunk_rows=1_000_000)
    sig = np.memmap(out / "signal.u16", dtype=np.uint16, mode="r").reshape(-1, 2)
    return out, meta, sig


def test_first_rows(converted):
    _, _, sig = converted
    assert np.array_equal(sig[:3], [[394, 747], [392, 750], [391, 746]])


def test_row_count_matches_csv(converted):
    _, meta, sig = converted
    with open(CSV) as f:
        n_lines = sum(1 for _ in f) - 1  # minus the header
    assert meta["samples"] == n_lines
    assert sig.shape == (n_lines, 2)


def test_file_size_is_4_bytes_per_row(converted):
    out, meta, _ = converted
    assert (out / "signal.u16").stat().st_size == meta["samples"] * 4


def test_all_values_match_csv(converted):
    _, _, sig = converted
    expected = pd.read_csv(CSV, dtype=np.int32).to_numpy()
    assert np.array_equal(sig, expected)


def test_random_access_across_chunk_border(converted):
    _, _, sig = converted
    expected = pd.read_csv(CSV, dtype=np.int32, skiprows=range(1, 999_951), nrows=100).to_numpy()
    assert np.array_equal(sig[999_950:1_000_050], expected)  # crosses the 1,000,000 row border