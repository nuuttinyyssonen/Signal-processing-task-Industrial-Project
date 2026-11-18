import numpy as np
from scipy.signal import find_peaks

def robust_noise(x):
    # Mediaani
    med = np.median(x)
    # Luvuista vähennetään mediaani ja negatiiviset luvut positiivisiksi
    distances = np.abs(x - med)
    mad = np.median(distances)
    return mad * 1.4826


def detect_peaks(x, fs, threshold_k=6.0, min_prominence=80.0, min_distance_ms=5.0):
    # Kohinataso
    noise = robust_noise(x)
    # Height = kerroin * kohina
    height = threshold_k * noise
    # Minimiväli millisekunneista näytteiksi
    distance = max(1,int(min_distance_ms / 1000 * fs))
    # Piikkien metskaus
    indices, properties = find_peaks(x, height=height, prominence=min_prominence, distance=distance)
    return indices, properties, noise