"""This script computes the descriptive statistics and the secondary analyses.

Input:  data/processed/scores_wide.csv and scores_long.csv (from src/clean_data.py)
Output (results/):
    descriptives.csv        mean and SD by method, and by method x part
    sample_description.csv  counts for the background questions
    secondary_tests.csv     post hoc tests by type of question (Holm-corrected), the order check,
                            and predicted vs. actual score

Usage:
    python src/secondary_analysis.py
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
QUESTION_TYPES = {"factual_pct": "Factual questions", "conceptual_pct": "Conceptual questions",
                  "covered_pct": "Questions fully covered by the AI summary"}


def paired(hw: pd.Series, ai: pd.Series, label: str) -> dict:
    """Paired t-test with the mean difference, its 95% CI and Cohen's d_z."""
    pairs = pd.DataFrame({"hw": hw, "ai": ai}).dropna()
    d = pairs["hw"] - pairs["ai"]
    res = stats.ttest_rel(pairs["hw"], pairs["ai"])
    ci = res.confidence_interval()
    return {"comparison": label, "n": len(d), "mean_handwritten": pairs["hw"].mean(),
            "mean_ai": pairs["ai"].mean(), "mean_diff": d.mean(), "ci95_low": ci.low, "ci95_high": ci.high,
            "t": res.statistic, "df": len(d) - 1, "p": res.pvalue,
            "cohens_dz": d.mean() / d.std(ddof=1) if d.std(ddof=1) > 0 else np.nan}


def holm(pvalues: list[float]) -> list[float]:
    """Holm-Bonferroni adjusted p-values."""
    order = np.argsort(pvalues)
    adjusted, running_max, m = np.empty(len(pvalues)), 0.0, len(pvalues)
    for rank, i in enumerate(order):
        running_max = max(running_max, min(1.0, (m - rank) * pvalues[i]))
        adjusted[i] = running_max
    return adjusted.tolist()


def describe(wide: pd.DataFrame, long: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for method in ("handwritten", "ai"):
        s = wide[f"{method}_score_pct"]
        rows.append({"method": method, "part": "both", "n": s.count(), "mean_pct": s.mean(), "sd_pct": s.std(ddof=1),
                     "mean_questions_correct": s.mean() * 6 / 100})
    for (method, video), g in long.groupby(["method", "video"]):
        rows.append({"method": method, "part": "Part 1" if video == "A" else "Part 2", "n": len(g),
                     "mean_pct": g["score_pct"].mean(), "sd_pct": g["score_pct"].std(ddof=1),
                     "mean_questions_correct": g["score_pct"].mean() * 6 / 100})
    return pd.DataFrame(rows)


def sample_description(wide: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for col in ["sequence", "age_range", "student_status", "native_english", "device",
                "usual_note_method", "ai_summary_use", "prior_knowledge"]:
        for value, n in wide[col].astype(str).value_counts().sort_index().items():
            rows.append({"question": col, "answer": value, "n": n})
    return pd.DataFrame(rows)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--processed-dir", type=Path, default=ROOT / "data" / "processed")
    parser.add_argument("--results-dir", type=Path, default=ROOT / "results")
    args = parser.parse_args(argv)
    wide = pd.read_csv(args.processed_dir / "scores_wide.csv")
    long = pd.read_csv(args.processed_dir / "scores_long.csv")
    args.results_dir.mkdir(parents=True, exist_ok=True)

    # First, simple descriptives of the scores and the sample
    describe(wide, long).to_csv(args.results_dir / "descriptives.csv", index=False)
    sample_description(wide).to_csv(args.results_dir / "sample_description.csv", index=False)

    # Then the post hoc tests: the same paired comparison for each type of question, Holm-corrected
    tests = [paired(wide[f"handwritten_{m}"], wide[f"ai_{m}"], label) for m, label in QUESTION_TYPES.items()]
    for row, p_adj in zip(tests, holm([t["p"] for t in tests])):
        row["p_holm"] = p_adj

    # We also check the order: is the handwritten advantage the same in both sequences? (Welch t-test)
    d1 = wide.loc[wide["sequence"] == 1, "diff_score_pct"]
    d2 = wide.loc[wide["sequence"] == 2, "diff_score_pct"]
    welch = stats.ttest_ind(d1, d2, equal_var=False)
    tests.append({"comparison": "Order check: difference in sequence 1 minus sequence 2", "n": len(d1) + len(d2),
                  "mean_diff": d1.mean() - d2.mean(), "t": welch.statistic, "df": welch.df, "p": welch.pvalue})

    # Finally, confidence: predicted minus actual score, compared between the two methods
    over_hw = wide["handwritten_predicted_pct"] - wide["handwritten_score_pct"]
    over_ai = wide["ai_predicted_pct"] - wide["ai_score_pct"]
    tests.append(paired(over_hw, over_ai, "Confidence: predicted minus actual score"))

    out = pd.DataFrame(tests)
    out.to_csv(args.results_dir / "secondary_tests.csv", index=False)
    print(out[["comparison", "n", "mean_diff", "p"] + (["p_holm"] if "p_holm" in out else [])].round(3).to_string(index=False))


if __name__ == "__main__":
    main()
