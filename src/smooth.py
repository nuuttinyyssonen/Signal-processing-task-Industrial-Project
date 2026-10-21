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