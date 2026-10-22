import numpy as np
import matplotlib.pyplot as plt
from check import get_samples_in_range
from baseline import remove_baseline

# Settings
SIGNAL_PATH = "data/example_out/signal.u16"
FS = 50_000 # Hz
START_S = 128
END_S = 140

# Get data between timestamps
samples = get_samples_in_range(SIGNAL_PATH, START_S, END_S)
print("samples shape:", samples.shape)

# Take adc2 only
adc2 = samples[:, 1]

t = np.arange(len(adc2)) / FS + START_S

# Visual
corrected, baseline = remove_baseline(adc2, FS, window_s=0.3)

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 7), sharex=True)

ax1.plot(t, adc2, linewidth=0.5, label="adc2")
ax1.plot(t, baseline, color="red", linewidth=1, label="baseline")
ax1.legend()
ax1.set_title("Ennen")

ax2.plot(t, corrected, linewidth=0.5)
ax2.set_title("Baseline poistettu")
ax2.set_xlabel("aika (s)")
plt.show()