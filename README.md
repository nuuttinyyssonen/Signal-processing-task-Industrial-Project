# Signal-processing-task-Industrial-Project

## Setup

The data is not stored in the repo (the `data/` folder is gitignored). To run the code:

1. Get the example signal CSV from moodle.
2. Put it in the `data/` folder and rename it to `example_signal.csv`
   (the original name `IDP_signal_example_[sami_dmitry_september2023].csv` contains
   square brackets that can cause problems in the terminal).
3. Install dependencies: `pip install numpy pandas pytest`

## Data conversion

`src/convert.py` reads the large signal CSV (columns `adc1,adc2`) in chunks, so the whole file is never loaded into memory, and writes the samples to a compact binary file (`signal.u16`, 2-byte unsigned integers, adc1 and adc2 interleaved) plus a `meta.json` with the sample count and sample rate.

Run from the repo root:

```
python src/convert.py data/example_signal.csv data/example_out
```

Output goes to `data/example_out/`. Requires `numpy` and `pandas`.

## Tests for data conversion

Run tests with:
`pytest -v`