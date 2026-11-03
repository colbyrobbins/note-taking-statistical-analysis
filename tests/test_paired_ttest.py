import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import paired_ttest as pt  # noqa: E402


def test_known_answer():
    # We compare the script with the t-test computed by hand
    hand = np.array([80, 70, 90, 60, 75.0])
    ai = np.array([70, 65, 80, 55, 70.0])
    res = pt.paired_tests(hand, ai)
    d = hand - ai
    t = d.mean() / (d.std(ddof=1) / np.sqrt(len(d)))
    assert res["t"] == pytest.approx(t)
    assert res["p_t"] == pytest.approx(2 * stats.t.sf(abs(t), len(d) - 1))
    assert res["cohens_dz"] == pytest.approx(d.mean() / d.std(ddof=1))
    half = stats.t.ppf(0.975, 4) * d.std(ddof=1) / np.sqrt(5)
    assert res["ci95_low"] == pytest.approx(d.mean() - half)
    assert res["ci95_high"] == pytest.approx(d.mean() + half)


def test_sign_is_handwritten_minus_ai():
    res = pt.paired_tests([90, 80, 85, 70], [60, 70, 65, 50])
    assert res["mean_diff"] > 0 and res["t"] > 0 and res["rank_biserial_r"] > 0
    assert pt.paired_tests([60, 70, 65, 50], [90, 80, 85, 70])["mean_diff"] < 0


def test_wilcoxon_treats_tied_scores_as_ties():
    # Scores like 100/6 carry floating-point noise; tied differences must still count as ties
    hand = np.array([100.0, 100.0, 100.0, 50.0, 100.0, 100 / 6 * 5])
    ai = np.array([100 - 100 / 6, 50.0, 100 / 3 * 2, 100 - 100 / 6, 100 / 6 * 4, 50.0])
    noisy = pt.paired_tests(hand, ai)["wilcoxon_p"]
    clean = pt.paired_tests(np.round(hand, 4), np.round(ai, 4))["wilcoxon_p"]
    assert noisy == pytest.approx(clean)


def test_too_few_pairs_gives_clear_error():
    with pytest.raises(ValueError, match="at least 2"):
        pt.paired_tests([80.0], [70.0])


def test_main_writes_one_result_row(tmp_path):
    wide = pd.DataFrame({"handwritten_score_pct": [100, 83.3, 66.7, 100, 83.3],
                         "ai_score_pct": [83.3, 66.7, 66.7, 50, 100]})
    wide.to_csv(tmp_path / "scores_wide.csv", index=False)
    pt.main(["--processed-dir", str(tmp_path), "--results-dir", str(tmp_path / "results")])
    row = pd.read_csv(tmp_path / "results" / "paired_ttest.csv").iloc[0]
    assert row["n_pairs"] == 5
    assert row["mean_diff"] == pytest.approx((wide["handwritten_score_pct"] - wide["ai_score_pct"]).mean())
