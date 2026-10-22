import argparse
import json
from pathlib import Path

import numpy as np
from scipy.ndimage import gaussian_filter1d, median_filter


def smooth_gaussian(x, sigma_s, fs):
    """Gaussian smoothing. sigma_s is the width in seconds, fs the sample rate."""
    return gaussian_filter1d(x.astype(np.float32), sigma=sigma_s * fs)


def smooth_median(x, window_s, fs):
    """Median smoothing. window_s is the window length in seconds."""
    window = max(3, int(window_s * fs))
    if window % 2 == 0:
        window += 1
    return median_filter(x.astype(np.float32), size=window)


def smooth_binary(signal_path, output_dir, sigma_s, chunk_samples=1_000_000):
    """Smooth each channel in a binary signal and write float32 output."""
    signal_path = Path(signal_path)
    output_dir = Path(output_dir)
    meta_path = signal_path.parent / "meta.json"
    if not meta_path.exists():
        raise FileNotFoundError(f"meta.json not found: {meta_path}")
    # Keep the original binary intact; smoothing writes a separate result.
    if output_dir.resolve() == signal_path.parent.resolve():
        raise ValueError("output_dir must differ from the input signal directory")
    if sigma_s <= 0:
        raise ValueError("sigma_s must be greater than zero")
    if chunk_samples <= 0:
        raise ValueError("chunk_samples must be greater than zero")

    input_meta = json.loads(meta_path.read_text(encoding="utf-8"))
    sample_rate = input_meta["sample_rate"]
    sample_count = input_meta["samples"]
    channels = input_meta["channels"]
    input_dtype = np.dtype(input_meta["dtype"])
    channel_count = len(channels)
    expected_bytes = sample_count * channel_count * input_dtype.itemsize
    if signal_path.stat().st_size != expected_bytes:
        raise ValueError("signal file size does not match its metadata")

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "signal.f32"
    source = np.memmap(signal_path, dtype=input_dtype, mode="r").reshape(
        sample_count, channel_count
    )
    output = np.memmap(
        output_path,
        dtype=np.float32,
        mode="w+",
        shape=(sample_count, channel_count),
    )

    # Read four sigma of extra context so filtering chunk edges does not create seams.
    sigma_samples = sigma_s * sample_rate
    overlap = int(4 * sigma_samples + 0.5)
    for start in range(0, sample_count, chunk_samples):
        end = min(start + chunk_samples, sample_count)
        read_start = max(0, start - overlap)
        read_end = min(sample_count, end + overlap)
        block = source[read_start:read_end]
        trim_start = start - read_start
        trim_end = trim_start + end - start
        for channel_index in range(channel_count):
            filtered = smooth_gaussian(block[:, channel_index], sigma_s, sample_rate)
            output[start:end, channel_index] = filtered[trim_start:trim_end]

    output.flush()
    # Record the output dtype so readers interpret the binary values correctly.
    output_meta = {
        **input_meta,
        "dtype": "float32",
        "smoothing": {"method": "gaussian", "sigma_s": sigma_s},
    }
    (output_dir / "meta.json").write_text(
        json.dumps(output_meta, indent=2), encoding="utf-8"
    )
    return output_meta


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gaussian-smooth a binary signal.")
    parser.add_argument("signal_path", help="Input binary signal path")
    parser.add_argument("output_dir", help="Separate output directory")
    parser.add_argument(
        "--sigma-ms", type=float, default=0.04,
        help="Gaussian sigma in milliseconds (default: 0.04)",
    )
    args = parser.parse_args()
    metadata = smooth_binary(
        args.signal_path,
        args.output_dir,
        sigma_s=args.sigma_ms / 1000,
    )
    print(f"Wrote {metadata['samples']:,} samples to {Path(args.output_dir) / 'signal.f32'}")