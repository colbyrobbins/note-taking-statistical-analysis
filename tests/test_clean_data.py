import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import clean_data  # noqa: E402


def test_scores_add_up_on_the_real_data(tmp_path):
    clean_data.main(["--out-dir", str(tmp_path)])
    items = pd.read_csv(tmp_path / "item_scores.csv")
    long = pd.read_csv(tmp_path / "scores_long.csv")
    wide = pd.read_csv(tmp_path / "scores_wide.csv")

    n = len(wide)
    assert len(items) == n * 12 and len(long) == n * 2
    assert np.allclose(long["score_pct"], 100 * long["n_correct"] / 6)
    # every person has one part per method, and the difference is handwritten minus AI
    assert (long.groupby("participant_id")["method"].nunique() == 2).all()
    assert np.allclose(wide["diff_score_pct"], wide["handwritten_score_pct"] - wide["ai_score_pct"])


def test_methods_follow_the_sequence(tmp_path):
    clean_data.main(["--out-dir", str(tmp_path)])
    long = pd.read_csv(tmp_path / "scores_long.csv")
    seq1_part1 = long[(long["sequence"] == 1) & (long["video"] == "A")]["method"]
    seq2_part1 = long[(long["sequence"] == 2) & (long["video"] == "A")]["method"]
    assert set(seq1_part1) == {"handwritten"} and set(seq2_part1) == {"ai"}
