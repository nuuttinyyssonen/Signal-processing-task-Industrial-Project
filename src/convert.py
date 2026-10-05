"""Convert a big 2-column signal CSV (adc1,adc2) to a binary file. """
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

SAMPLE_RATE = 50_000


def convert_csv(csv_path, out_dir, chunk_rows=5_000_000, sample_rate=SAMPLE_RATE):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    total = 0
    t0 = time.time()

    with open(out / "signal.u16", "wb") as f:
        for chunk in pd.read_csv(csv_path, chunksize=chunk_rows, dtype=np.int32):
            a = chunk.to_numpy().astype(np.uint16)  # shape (n, 2)
            a.tofile(f)
            total += len(a)
            print(f"{total:,} rows ({time.time() - t0:.0f} s)", end="\r")

    meta = {"samples": total, "sample_rate": sample_rate,
            "channels": ["adc1", "adc2"], "dtype": "uint16"}
    (out / "meta.json").write_text(json.dumps(meta, indent=2))
    print(f"\nDone: {total:,} samples in {time.time() - t0:.1f} s")
    return meta


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("usage: python convert.py <input.csv> <output_dir>")
    convert_csv(sys.argv[1], sys.argv[2])