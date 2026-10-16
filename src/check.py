import numpy as np
import json
from pathlib import Path

def get_samples_in_range(signal_path, start_time_s, end_time_s, sample_rate=None):
    """Return both signal channels for the requested time range."""
    # Find the metadata file next to the signal file.
    signal_path = Path(signal_path)
    meta_path = signal_path.parent / "meta.json"

    # The sample rate is needed to convert seconds into sample indexes.
    if not meta_path.exists():
        raise FileNotFoundError(f"meta.json not found: {meta_path}")

    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    sample_rate = sample_rate or meta.get("sample_rate")

    if sample_rate is None:
        raise ValueError("sample_rate not found, please provide it explicitly or check meta.json")

    # Convert the start and end times from seconds to sample indexes.
    start_idx = int(start_time_s * sample_rate)
    end_idx = int(end_time_s * sample_rate)

    # Read the binary file as rows with two channels: adc1 and adc2.
    signal = np.memmap(signal_path, dtype=np.uint16, mode="r").reshape(-1, 2)

    # Keep the indexes inside the available signal data.
    start_idx = max(0, start_idx)
    end_idx = min(len(signal), end_idx)

    # Return the rows from the start index up to (but not including) the end index.
    return signal[start_idx:end_idx]

#Example usage of the function (poistetaan myöhemmin)
if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    signal_path = root / "data" / "example_out" / "signal.u16"

    samples = get_samples_in_range(
        signal_path,
        start_time_s=0.5,
        end_time_s=1.5,
        sample_rate=50_000
    )
    print(samples.shape)
    print(samples[:5])