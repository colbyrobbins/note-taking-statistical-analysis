import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import secondary_analysis as sa  # noqa: E402


def test_holm_matches_hand_calculation():
    # sorted p: .01 x3 = .03, .03 x2 = .06, .04 x1 = .04 -> kept monotone at .06
    assert np.allclose(sa.holm([0.01, 0.04, 0.03]), [0.03, 0.06, 0.06])


def test_paired_difference_is_handwritten_minus_ai():
    row = sa.paired(pd.Series([100.0, 83.3, 66.7, 100.0]), pd.Series([83.3, 66.7, 66.7, 50.0]), "x")
    assert row["mean_diff"] > 0 and row["ci95_low"] < row["mean_diff"] < row["ci95_high"]
