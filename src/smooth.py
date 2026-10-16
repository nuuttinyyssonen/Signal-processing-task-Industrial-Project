import numpy as np
from scipy.ndimage import gaussian_filter1d
from scipy.signal import savgol_filter


def smooth_gaussian(x, sigma_s, fs):
    """Gaussian smoothing. sigma_s is the width in seconds, fs the sample rate."""
    return gaussian_filter1d(x.astype(np.float32), sigma=sigma_s * fs)


def smooth_savgol(x, window_s, fs, polyorder=3):
    """Savitzky-Golay smoothing. window_s is the window length in seconds."""
    window = int(window_s * fs) | 1   # window length must be odd
    return savgol_filter(x.astype(np.float32), window, polyorder)