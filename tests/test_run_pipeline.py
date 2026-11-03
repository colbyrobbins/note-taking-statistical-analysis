import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import clean_data  # noqa: E402
import make_figures  # noqa: E402
import paired_ttest  # noqa: E402


def test_final_numbers_match_the_report(tmp_path):
    # We run the main steps on the committed raw data, into a temp folder
    clean_data.main(["--out-dir", str(tmp_path / "processed")])
    paired_ttest.main(["--processed-dir", str(tmp_path / "processed"), "--results-dir", str(tmp_path / "results")])
    row = pd.read_csv(tmp_path / "results" / "paired_ttest.csv").iloc[0]
    assert row["n_pairs"] == 16
    assert row["mean_diff"] == pytest.approx(14.583, abs=0.01)
    assert row["p_t"] == pytest.approx(0.043, abs=0.001)
    assert row["wilcoxon_p"] == pytest.approx(0.057, abs=0.001)

    make_figures.main(["--processed-dir", str(tmp_path / "processed"), "--out-dir", str(tmp_path / "figures")])
    assert len(list((tmp_path / "figures").glob("*.png"))) == 6
