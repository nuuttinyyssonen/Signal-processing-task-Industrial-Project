import numpy as np
import pandas as pd

def remove_baseline(signal, fs, window_s=0.3):
    "Remove baseline using a rolling median"

    x = signal.astype(np.float64)
    window = int(window_s * fs)

    baseline = (
        pd.Series(x)
        .rolling(window, center=True, min_periods=1)
        .median()
        .to_numpy()
    )

    return x - baseline, baseline