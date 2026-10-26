import numpy as np
import pandas as pd
from scipy import stats

import analyze
import assign_conditions
import clean_data
import power_analysis
import simulate_data


def test_assignments_are_balanced():
    df = assign_conditions.build_assignments(40, seed=1)
    per_participant = df.drop_duplicates("participant_id")
    assert per_participant["sequence"].value_counts().nunique() == 1  # 10 each
    # every participant gets both videos and both methods
    for _, g in df.groupby("participant_id"):
        assert set(g["video"]) == {"A", "B"}
        assert set(g["method"]) == {"handwritten", "ai"}


def test_power_analysis_matches_planned_sample():
    assert power_analysis.required_n(0.6) in (24, 25)


def test_paired_analysis_matches_scipy_and_is_two_tailed():
    rng = np.random.default_rng(0)
    hand = rng.normal(60, 10, 25)
    ai = hand + rng.normal(3, 8, 25)
    res = analyze.paired_analysis(hand, ai)
    ref = stats.ttest_rel(ai, hand)  # scipy default is two-sided
    assert np.isclose(res["t"], ref.statistic)
    assert np.isclose(res["p_two_tailed"], ref.pvalue)
    assert res["ci95_low"] < res["mean_diff_ai_minus_hand"] < res["ci95_high"]


def test_end_to_end_on_simulated_data(tmp_path):
    raw, proc, res = tmp_path / "raw", tmp_path / "proc", tmp_path / "results"
    simulate_data.main(["--n", "40", "--effect", "0.5", "--dropout", "0.1", "--out-dir", str(raw)])
    clean_data.main(["--raw-dir", str(raw), "--out-dir", str(proc), "--results-dir", str(res)])

    wide = pd.read_csv(proc / "scores_wide.csv")
    assert 30 <= len(wide) <= 40  # some dropouts excluded
    assert wide.filter(like="_delayed").notna().all().all()
    assert (tmp_path / "results" / "tables" / "exclusions.csv").exists()

    analyze.main(["--data-dir", str(proc), "--results-dir", str(res)])
    out = pd.read_csv(res / "tables" / "primary_results.csv")
    assert list(out["analysis"]) == ["primary", "secondary"]
    assert out.loc[0, "df"] == out.loc[0, "n_pairs"] - 1
