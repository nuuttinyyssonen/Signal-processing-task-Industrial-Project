# Signal-processing-task-Industrial-Project

## Setup

The data is not stored in the repo (the `data/` folder is gitignored). To run the code:

1. Get the example signal CSV from moodle.
2. Put it in the `data/` folder and rename it to `example_signal.csv`
   (the original name `IDP_signal_example_[sami_dmitry_september2023].csv` contains
   square brackets that can cause problems in the terminal).
3. Install dependencies: `pip install numpy pandas scipy matplotlib pytest customtkinter`

 !!! ADDED customtkinter to dependencies !!!

 ## Running the application
 `python src/main.py`

## Data conversion

`src/convert.py` reads the large signal CSV (columns `adc1,adc2`) in chunks, so the whole file is never loaded into memory, and writes the samples to a compact binary file (`signal.u16`, 2-byte unsigned integers, adc1 and adc2 interleaved) plus a `meta.json` with the sample count and sample rate.

Run from the repo root:

```
python src/convert.py data/example_signal.csv data/example_out
```

Output goes to `data/example_out/`. Requires `numpy` and `pandas`.

## Gaussian smoothing

Smooth each channel in the converted binary and write a separate `float32` output directory:

```
python src/smooth.py data/example_out/signal.u16 data/smoothed_out --sigma-ms 0.04
```

The output contains an interleaved `signal.f32` file and a `meta.json` recording the dtype and smoothing settings. The input binary is left unchanged. The default sigma is 0.04 ms (2 samples at 50 kHz); adjust it for the signal and verify the result with `src/compare_smoothing.py`. Use `get_samples_in_range` from `check.py` to read time ranges from either the original `uint16` data or smoothed `float32` output; it selects the format from metadata.

## Tests for data conversion

Run tests with:
`pytest -v`
