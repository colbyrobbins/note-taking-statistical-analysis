import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import power_analysis as pa  # noqa: E402


def test_planned_sample_size_matches_gpower():
    # G*Power gives n = 24 (power 0.804) for d_z = 0.6, alpha = 0.05 two-tailed, power = 0.80
    assert pa.required_n(0.6) == 24
    assert abs(pa.paired_t_power(24, 0.6) - 0.804) < 0.001


def test_power_grows_with_n_and_effect():
    assert pa.paired_t_power(30, 0.6) > pa.paired_t_power(24, 0.6)
    assert pa.paired_t_power(24, 0.8) > pa.paired_t_power(24, 0.6)
    assert pa.required_n(0.4) > pa.required_n(0.6)


def test_detectable_effect_is_consistent_with_required_n():
    dz = pa.detectable_dz(24)
    assert 0.59 < dz < 0.61
    assert abs(pa.paired_t_power(24, dz) - 0.80) < 1e-6


def test_outputs_are_written(tmp_path):
    pa.main(["--results-dir", str(tmp_path)])
    assert (tmp_path / "power_required_n.csv").exists()
    assert (tmp_path / "power_sensitivity.csv").exists()
    assert (tmp_path / "figures" / "power_curve.png").exists()
