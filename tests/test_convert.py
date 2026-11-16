from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from convert import conversion_cache_dir, convert_csv

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


def test_conversion_reports_progress_after_each_chunk(tmp_path):
    source = tmp_path / "signal.csv"
    pd.DataFrame({"adc1": [1, 2, 3, 4, 5], "adc2": [6, 7, 8, 9, 10]}).to_csv(
        source,
        index=False,
    )
    progress = []

    meta = convert_csv(
        source,
        tmp_path / "converted",
        chunk_rows=2,
        progress_callback=lambda rows, elapsed: progress.append((rows, elapsed)),
    )

    assert meta["samples"] == 5
    assert [rows for rows, _ in progress] == [2, 4, 5]


def test_conversion_cache_is_outside_source_directory_and_unique(tmp_path):
    source_dir = tmp_path / "read-only-source"
    source_dir.mkdir()
    source = source_dir / "large signal.csv"
    source.write_text("adc1,adc2\n1,2\n", encoding="utf-8")
    cache_root = tmp_path / "writable-cache"

    cache_dir = conversion_cache_dir(source, cache_root=cache_root)

    assert cache_dir.is_relative_to(cache_root)
    assert not cache_dir.is_relative_to(source_dir)
    assert cache_dir == conversion_cache_dir(source, cache_root=cache_root)

    source.write_text("adc1,adc2\n1,2\n3,4\n", encoding="utf-8")
    assert conversion_cache_dir(source, cache_root=cache_root) != cache_dir