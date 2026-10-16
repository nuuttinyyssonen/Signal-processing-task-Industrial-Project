import numpy as np
from scipy.ndimage import gaussian_filter1d


def smooth_gaussian(x, sigma_s, fs):
    """Gaussian smoothing. sigma_s is the width in seconds, fs the sample rate."""
    return gaussian_filter1d(x.astype(np.float32), sigma=sigma_s * fs)