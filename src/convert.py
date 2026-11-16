"""Convert a big 2-column signal CSV (adc1,adc2) to a binary file. """
import json
import hashlib
import os
import sys
import time
from collections.abc import Callable
from pathlib import Path

import numpy as np
import pandas as pd

SAMPLE_RATE = 50_000


def conversion_cache_dir(csv_path, cache_root=None):
    """Return a writable per-user cache directory for a source CSV."""
    source = Path(csv_path).expanduser().resolve(strict=True)
    if cache_root is None:
        if sys.platform == "darwin":
            cache_root = Path.home() / "Library" / "Caches" / "SignalViewer"
        elif os.name == "nt":
            cache_root = Path(
                os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")
            ) / "SignalViewer"
        else:
            cache_root = Path(
                os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")
            ) / "signal-viewer"

    stat = source.stat()
    fingerprint = hashlib.sha256(
        f"{source}\0{stat.st_size}\0{stat.st_mtime_ns}".encode("utf-8")
    ).hexdigest()[:16]
    return Path(cache_root) / "converted" / f"{source.stem[:60]}-{fingerprint}"


def convert_csv(
    csv_path,
    out_dir,
    chunk_rows=1_000_000,
    sample_rate=SAMPLE_RATE,
    progress_callback: Callable[[int, float], None] | None = None,
):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    total = 0
    t0 = time.time()

    with open(out / "signal.u16", "wb") as f:
        for chunk in pd.read_csv(csv_path, chunksize=chunk_rows, dtype=np.int32):
            a = chunk.to_numpy().astype(np.uint16)  # shape (n, 2)
            a.tofile(f)
            total += len(a)
            elapsed = time.time() - t0
            print(f"{total:,} rows ({elapsed:.0f} s)", end="\r")
            if progress_callback is not None:
                progress_callback(total, elapsed)

    meta = {"samples": total, "sample_rate": sample_rate,
            "channels": ["adc1", "adc2"], "dtype": "uint16"}
    (out / "meta.json").write_text(json.dumps(meta, indent=2))
    print(f"\nDone: {total:,} samples in {time.time() - t0:.1f} s")
    return meta


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("usage: python convert.py <input.csv> <output_dir>")
    convert_csv(sys.argv[1], sys.argv[2])