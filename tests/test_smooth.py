import json
import numpy as np
from smooth import smooth_binary, smooth_gaussian

def test_smooth_binary_writes_chunked_float32_output(tmp_path):
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "smoothed"
    input_dir.mkdir()
    signal = np.zeros((23, 2), dtype=np.uint16)
    signal[10, 0] = 100
    signal[15, 1] = 80
    signal_path = input_dir / "signal.u16"
    signal.tofile(signal_path)
    metadata = {
        "samples": len(signal),
        "sample_rate": 1000,
        "channels": ["adc1", "adc2"],
        "dtype": "uint16",
    }
    (input_dir / "meta.json").write_text(json.dumps(metadata), encoding="utf-8")

    result = smooth_binary(signal_path, output_dir, sigma_s=0.002, chunk_samples=7)

    output = np.memmap(output_dir / "signal.f32", dtype=np.float32, mode="r").reshape(-1, 2)
    expected = np.column_stack(
        [smooth_gaussian(signal[:, index], 0.002, 1000) for index in range(2)]
    )
    assert np.allclose(output, expected)
    assert result["dtype"] == "float32"
    assert result["smoothing"] == {"method": "gaussian", "sigma_s": 0.002}
    assert np.array_equal(np.fromfile(signal_path, dtype=np.uint16).reshape(-1, 2), signal)