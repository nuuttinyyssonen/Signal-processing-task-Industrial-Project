import numpy as np
sig = np.memmap("data/example_out/signal.u16", dtype=np.uint16, mode="r").reshape(-1, 2)
print(sig.shape)
print(sig[:6])
