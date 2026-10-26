"""Statistical analysis: handwritten vs AI-generated notes.

H0: mean quiz score is the same for handwritten and AI notes (mu_diff = 0).
H1: the means differ (two-tailed; AI could be better OR worse).

Primary (confirmatory):  48-hour delayed quiz, two-tailed paired t-test.
Secondary (exploratory): immediate quiz, same test. Not corrected for multiplicity.

Usage:
    python src/analyze.py

Writes results/tables/primary_results.csv and results/tables/assumption_checks.csv.
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from config import ALPHA, DATA_PROCESSED, PRIMARY_TIMEPOINT, RESULTS, SECONDARY_TIMEPOINT


def paired_analysis(hand, ai, alpha=ALPHA):
    """Two-tailed paired t-test of AI minus handwritten, with CI and effect sizes."""
    hand = np.asarray(hand, dtype=float)
    ai = np.asarray(ai, dtype=float)
    diff = ai - hand
    n = len(diff)
    df = n - 1
    mean_diff = diff.mean()
    sd_diff = diff.std(ddof=1)
    se = sd_diff / np.sqrt(n)
    t_stat, p_value = stats.ttest_rel(ai, hand, alternative="two-sided")
    t_crit = stats.t.ppf(1 - alpha / 2, df)
    dz = mean_diff / sd_diff if sd_diff > 0 else np.nan
    hedges_gz = dz * (1 - 3 / (4 * df - 1)) if df > 1 else np.nan
    return {
        "n_pairs": n,
        "mean_handwritten": hand.mean(),
        "mean_ai": ai.mean(),
        "mean_diff_ai_minus_hand": mean_diff,
        "sd_diff": sd_diff,
        "t": t_stat,
        "df": df,
        "p_two_tailed": p_value,
        "ci95_low": mean_diff - t_crit * se,
        "ci95_high": mean_diff + t_crit * se,
        "cohens_dz": dz,
        "hedges_gz": hedges_gz,
    }


def assumption_checks(hand, ai, first_method=None):
    """Normality of differences, a non-parametric backup, and an order check."""
    diff = np.asarray(ai, dtype=float) - np.asarray(hand, dtype=float)
    shapiro_p = stats.shapiro(diff).pvalue if len(diff) >= 3 else np.nan
    try:
        wilcoxon_p = stats.wilcoxon(diff, alternative="two-sided").pvalue
    except ValueError:  # all differences zero
        wilcoxon_p = np.nan

    order_p = np.nan
    if first_method is not None:
        fm = np.asarray(first_method)
        g_ai, g_hand = diff[fm == "ai"], diff[fm == "handwritten"]
        if len(g_ai) >= 2 and len(g_hand) >= 2:
            # In a crossover, a period/order effect shows up as different mean
            # differences between "AI first" and "handwritten first" participants.
            order_p = stats.ttest_ind(g_ai, g_hand, equal_var=False).pvalue
    return {
        "shapiro_p_differences": shapiro_p,
        "wilcoxon_signed_rank_p": wilcoxon_p,
        "order_effect_welch_p": order_p,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DATA_PROCESSED)
    parser.add_argument("--results-dir", type=Path, default=RESULTS)
    args = parser.parse_args(argv)

    wide = pd.read_csv(args.data_dir / "scores_wide.csv")
    results, checks = [], []
    for label, tp in (("primary", PRIMARY_TIMEPOINT), ("secondary", SECONDARY_TIMEPOINT)):
        res = paired_analysis(wide[f"handwritten_{tp}"], wide[f"ai_{tp}"])
        chk = assumption_checks(wide[f"handwritten_{tp}"], wide[f"ai_{tp}"], wide["first_method"])
        results.append({"analysis": label, "timepoint": tp, **res})
        checks.append({"analysis": label, "timepoint": tp, **chk})

    tables = args.results_dir / "tables"
    tables.mkdir(parents=True, exist_ok=True)
    res_df, chk_df = pd.DataFrame(results), pd.DataFrame(checks)
    res_df.to_csv(tables / "primary_results.csv", index=False)
    chk_df.to_csv(tables / "assumption_checks.csv", index=False)

    pd.set_option("display.width", 200)
    print(res_df.round(4).T.to_string(header=False))
    print()
    print(chk_df.round(4).T.to_string(header=False))


if __name__ == "__main__":
    main()
