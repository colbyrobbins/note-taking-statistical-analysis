"""This script runs the main test of the study: a two-tailed paired t-test.

Each participant has two scores, one with handwritten notes and one with the AI summary, so we
compare them in pairs. The steps are:
    1. take each person's difference (handwritten minus AI)
    2. check the differences: Shapiro-Wilk test for normality and outliers (|z| > 3)
    3. two-tailed paired t-test, alpha = 0.05: mean difference with 95% CI, t, df, p, Cohen's d_z
    4. Wilcoxon signed-rank test (with rank-biserial r), which does not assume normal differences

Input:  data/processed/scores_wide.csv (from src/clean_data.py)
Output: results/paired_ttest.csv, one row with all the numbers above

Usage:
    python src/paired_ttest.py
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
ALPHA = 0.05


def paired_tests(handwritten, ai) -> dict:
    """Paired t-test (two-tailed), the assumption checks and the Wilcoxon signed-rank test."""
    handwritten = np.asarray(handwritten, dtype=float)
    ai = np.asarray(ai, dtype=float)
    d = handwritten - ai
    n = len(d)
    if n < 2:
        raise ValueError(f"Need at least 2 complete pairs for a paired t-test; got {n}.")
    mean, sd = d.mean(), d.std(ddof=1)

    # First the paired t-test with its 95% confidence interval
    t_res = stats.ttest_rel(handwritten, ai, alternative="two-sided")
    ci = t_res.confidence_interval(confidence_level=1 - ALPHA)

    # Then we check the assumptions: are the differences roughly normal, and are there outliers?
    shapiro_p = stats.shapiro(d).pvalue if n >= 3 and sd > 0 else np.nan
    n_outliers = int((np.abs((d - mean) / sd) > 3).sum()) if sd > 0 else 0

    # We also run the Wilcoxon test. Scores move in steps of 1/6, so many differences are tied;
    # rounding removes floating-point noise, and with up to 20 pairs the p-value is exact.
    nonzero = np.round(d, 8)
    nonzero = nonzero[nonzero != 0]
    if len(nonzero):
        method = stats.PermutationMethod(n_resamples=np.inf) if len(nonzero) <= 20 else "approx"
        w = stats.wilcoxon(nonzero, alternative="two-sided", method=method)
        ranks = stats.rankdata(np.abs(nonzero))
        rank_biserial = (ranks[nonzero > 0].sum() - ranks[nonzero < 0].sum()) / ranks.sum()
        w_stat, w_p = float(w.statistic), float(w.pvalue)
    else:
        w_stat = w_p = rank_biserial = np.nan

    return {
        "n_pairs": n,
        "mean_handwritten": handwritten.mean(),
        "mean_ai": ai.mean(),
        "mean_diff": mean,
        "sd_diff": sd,
        "ci95_low": float(ci.low),
        "ci95_high": float(ci.high),
        "t": float(t_res.statistic),
        "df": n - 1,
        "p_t": float(t_res.pvalue),
        "cohens_dz": mean / sd if sd > 0 else np.nan,
        "shapiro_p": shapiro_p,
        "n_outliers_z3": n_outliers,
        "wilcoxon_stat": w_stat,
        "wilcoxon_p": w_p,
        "rank_biserial_r": rank_biserial,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--processed-dir", type=Path, default=ROOT / "data" / "processed")
    parser.add_argument("--results-dir", type=Path, default=ROOT / "results")
    args = parser.parse_args(argv)

    # We read each person's two scores and run the tests
    wide = pd.read_csv(args.processed_dir / "scores_wide.csv")
    result = paired_tests(wide["handwritten_score_pct"], wide["ai_score_pct"])

    args.results_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([result]).to_csv(args.results_dir / "paired_ttest.csv", index=False)

    print(f"{result['n_pairs']} participants analysed")
    print(f"Mean diff (handwritten - AI) = {result['mean_diff']:.2f} points, "
          f"95% CI [{result['ci95_low']:.2f}, {result['ci95_high']:.2f}]")
    print(f"Paired t({result['df']}) = {result['t']:.3f}, p = {result['p_t']:.4f}, d_z = {result['cohens_dz']:.2f}")
    print(f"Shapiro-Wilk p = {result['shapiro_p']:.4f}; Wilcoxon p = {result['wilcoxon_p']:.4f}, "
          f"r = {result['rank_biserial_r']:.2f}")


if __name__ == "__main__":
    main()
