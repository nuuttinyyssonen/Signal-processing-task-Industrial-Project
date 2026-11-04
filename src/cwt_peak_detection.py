from dataclasses import dataclass
from collections.abc import Sequence
from typing import Literal

import numpy as np
from scipy.signal import find_peaks, find_peaks_cwt


@dataclass(frozen=True)
class Peak:
    index: int
    time: float
    amplitude: float
    prominence: float
    polarity: Literal["up", "down"]


def detect_peaks_cwt(
    signal: Sequence[float] | np.ndarray,
    sample_rate: float,
    widths: Sequence[float] = tuple(range(100, 1001, 100)),
    *,
    min_prominence: float = 100.0,
    min_distance_s: float = 0.3,
    min_height: float = 50.0,
    min_snr: float = 1.0,
    polarity: Literal["up", "down", "both"] = "up",
    chunk_size: int = 1_000_000,
) -> list[Peak]:
    """Find and confirm peaks in bounded chunks of a one-dimensional signal."""
    values = np.asanyarray(signal)
    if values.ndim != 1:
        raise ValueError("signal must be one-dimensional")
    if not np.isfinite(sample_rate) or sample_rate <= 0:
        raise ValueError("sample_rate must be positive and finite")
    if not isinstance(chunk_size, (int, np.integer)) or chunk_size <= 0:
        raise ValueError("chunk_size must be a positive integer")

    cwt_widths = np.asarray(widths, dtype=np.float64)
    if cwt_widths.ndim != 1 or cwt_widths.size == 0:
        raise ValueError("widths must be a non-empty one-dimensional sequence")
    if not np.all(np.isfinite(cwt_widths)) or np.any(cwt_widths <= 0):
        raise ValueError("widths must contain only positive finite values")
    if not np.isfinite(min_prominence) or min_prominence < 0:
        raise ValueError("min_prominence must be non-negative and finite")
    if not np.isfinite(min_distance_s) or min_distance_s < 0:
        raise ValueError("min_distance_s must be non-negative and finite")
    if not np.isfinite(min_height) or min_height < 0:
        raise ValueError("min_height must be non-negative and finite")
    if not np.isfinite(min_snr) or min_snr <= 0:
        raise ValueError("min_snr must be positive and finite")
    if polarity not in ("up", "down", "both"):
        raise ValueError("polarity must be 'up', 'down', or 'both'")
    if values.size == 0:
        return []

    distance = max(1, int(round(sample_rate * min_distance_s)))
    downsample_factor = max(1, int(np.ceil(np.max(cwt_widths) / 20)))
    cwt_radius = int(np.ceil(5 * np.max(cwt_widths)))
    halo = max(distance, cwt_radius)
    directions = ("up", "down") if polarity == "both" else (polarity,)
    detected: list[Peak] = []

    for direction in directions:
        for core_start in range(0, values.size, chunk_size):
            core_end = min(core_start + chunk_size, values.size)
            read_start = max(0, core_start - halo)
            read_end = min(values.size, core_end + halo)
            raw_chunk = np.asarray(values[read_start:read_end], dtype=np.float64)
            if not np.all(np.isfinite(raw_chunk)):
                raise ValueError("signal must contain only finite values")

            core_left = core_start - read_start
            core_right = core_end - read_start
            baseline = float(np.median(raw_chunk[core_left:core_right]))
            working_signal = raw_chunk - baseline
            if direction == "down":
                working_signal = -working_signal

            candidates, properties = find_peaks(
                working_signal,
                prominence=min_prominence,
                distance=distance,
            )
            in_core = (candidates >= core_left) & (candidates < core_right)
            for candidate, prominence in zip(
                candidates[in_core],
                properties["prominences"][in_core],
            ):
                if working_signal[candidate] < min_height:
                    continue
                global_candidate = read_start + int(candidate)
                cwt_start = max(0, global_candidate - cwt_radius)
                cwt_end = min(values.size, global_candidate + cwt_radius + 1)
                raw_segment = np.asarray(
                    values[cwt_start:cwt_end],
                    dtype=np.float64,
                )
                working_segment = raw_segment - baseline
                if direction == "down":
                    working_segment = -working_segment
                segment = working_segment[::downsample_factor]
                local_widths = np.maximum(1, cwt_widths / downsample_factor)
                cwt_candidates = find_peaks_cwt(
                    segment,
                    local_widths,
                    min_snr=min_snr,
                )
                if any(
                    abs(
                        cwt_start
                        + int(cwt_candidate) * downsample_factor
                        - global_candidate
                    )
                    <= max(distance, int(np.max(cwt_widths)))
                    for cwt_candidate in cwt_candidates
                ):
                    detected.append(
                        Peak(
                            index=global_candidate,
                            time=float(global_candidate / sample_rate),
                            amplitude=float(values[global_candidate]),
                            prominence=float(prominence),
                            polarity=direction,
                        )
                    )

    return sorted(detected, key=lambda peak: (peak.index, peak.polarity))
