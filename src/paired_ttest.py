"""Primary analysis: two-tailed paired t-test, handwritten notes vs. AI summary.

Follows the "Primary analysis" section of docs/analysis_plan.md:
    1. score each part as % correct and take each person's difference (handwritten minus AI)
    2. check the differences: Shapiro-Wilk test and outliers (|z| > 3)
    3. two-tailed paired t-test, alpha = 0.05: mean difference with 95% CI, t, df, p, Cohen's d_z
    4. Wilcoxon signed-rank test (with rank-biserial r), reported every time; it is used for the
       decision instead of the t-test when Shapiro-Wilk p < .05

Input (data/raw/, written by src/ingest_app_data.py):
    quiz_responses.csv, assignments.csv, answer_key.csv, participants.csv, session_process.csv
Output:
    results/paired_ttest.csv   one row with the numbers above plus how many people were analysed

People who meet any exclusion rule in the analysis plan are dropped entirely. With --no-exclusions
everyone with a complete pair is analysed (the plan's sensitivity check) and the output goes to
results/paired_ttest_no_exclusions.csv, so the primary file is never overwritten.

Usage:
    python src/paired_ttest.py                  # primary analysis, exclusions applied
    python src/paired_ttest.py --no-exclusions  # sensitivity run, all complete participants
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = ROOT / "data" / "raw"
RESULTS = ROOT / "results"
MATERIALS = ROOT / "materials" / "study_materials.json"

ALPHA = 0.05


def read_table(raw_dir: Path, name: str) -> pd.DataFrame:
    return pd.read_csv(raw_dir / name, dtype=str)


def part_seconds(materials: dict) -> dict:
    """Length of each part of the video in seconds, e.g. {"A": 137, "B": 98}."""
    return {k: v["end"] - v["start"] for k, v in materials["parts"].items()}


def score_parts(quiz: pd.DataFrame, key: pd.DataFrame) -> pd.DataFrame:
    """% correct for each participant x part (video A/B)."""
    q_cols = [c for c in quiz.columns if c.startswith("q") and c[1:].isdigit()]
    long = quiz.melt(id_vars=["participant_id", "video"], value_vars=q_cols,
                     var_name="question_id", value_name="response")
    long = long.merge(key[["video", "question_id", "correct_answer"]], on=["video", "question_id"])
    long["correct"] = (long["response"].astype(str).str.strip().str.upper()
                       == long["correct_answer"].astype(str).str.strip().str.upper())
    scores = long.groupby(["participant_id", "video"], as_index=False)["correct"].mean()
    scores["pct"] = scores["correct"] * 100
    return scores[["participant_id", "video", "pct"]]


def method_scores(scores: pd.DataFrame, assignments: pd.DataFrame) -> pd.DataFrame:
    """One row per participant with their handwritten and AI score and the difference."""
    merged = scores.merge(assignments[["participant_id", "video", "method"]], on=["participant_id", "video"])
    wide = merged.pivot(index="participant_id", columns="method", values="pct")
    wide = wide.dropna(subset=["handwritten", "ai"])
    wide["diff"] = wide["handwritten"] - wide["ai"]
    return wide[["handwritten", "ai", "diff"]]


def _is(series: pd.Series, value: str) -> pd.Series:
    return series.astype(str).str.strip().str.lower() == value.lower()


def exclusion_flags(participants: pd.DataFrame, process: pd.DataFrame, seconds: dict) -> pd.DataFrame:
    """One row per participant, one True/False column per exclusion rule in the analysis plan."""
    p = participants.set_index("participant_id")
    flags = pd.DataFrame(index=p.index)
    flags["prior_knowledge_high"] = pd.to_numeric(p["prior_knowledge"], errors="coerce") >= 4
    flags["failed_attention_check"] = ~_is(p["attention_check"], "often")

    proc = process.copy()
    proc["short_watch"] = pd.to_numeric(proc["watch_seconds"], errors="coerce") < proc["video"].map(seconds)
    proc["did_not_follow_method"] = _is(proc["compliance"], "no")
    proc["ai_part_wrote_notes"] = _is(proc["ai_part_wrote_notes"], "yes")
    proc["used_material_in_quiz"] = _is(proc["used_material_during_quiz"], "yes")
    rules = ["short_watch", "did_not_follow_method", "ai_part_wrote_notes", "used_material_in_quiz"]
    flags = flags.join(proc.groupby("participant_id")[rules].any())
    return flags.fillna(False).astype(bool)


def paired_tests(handwritten, ai) -> dict:
    """Paired t-test (two-tailed) plus assumption checks and the Wilcoxon signed-rank test."""
    handwritten = np.asarray(handwritten, dtype=float)
    ai = np.asarray(ai, dtype=float)
    d = handwritten - ai
    n = len(d)
    if n < 2:
        raise ValueError(f"Need at least 2 complete pairs for a paired t-test; got {n}.")
    mean, sd = d.mean(), d.std(ddof=1)

    t_res = stats.ttest_rel(handwritten, ai, alternative="two-sided")
    ci = t_res.confidence_interval(confidence_level=1 - ALPHA)

    shapiro_p = stats.shapiro(d).pvalue if n >= 3 and sd > 0 else np.nan
    n_outliers = int((np.abs((d - mean) / sd) > 3).sum()) if sd > 0 else 0

    nonzero = d[d != 0]
    if len(nonzero):
        w = stats.wilcoxon(nonzero, alternative="two-sided")
        ranks = stats.rankdata(np.abs(nonzero))
        rank_biserial = (ranks[nonzero > 0].sum() - ranks[nonzero < 0].sum()) / ranks.sum()
        w_stat, w_p = float(w.statistic), float(w.pvalue)
    else:
        w_stat = w_p = rank_biserial = np.nan

    decision = "wilcoxon" if shapiro_p < ALPHA else "paired_t"
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
        "decision_test": decision,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=DATA_RAW)
    parser.add_argument("--results-dir", type=Path, default=RESULTS)
    parser.add_argument("--materials", type=Path, default=MATERIALS)
    parser.add_argument("--no-exclusions", action="store_true",
                        help="analyse everyone with a complete pair (sensitivity run)")
    args = parser.parse_args(argv)

    materials = json.loads(args.materials.read_text(encoding="utf-8"))
    table = {n: read_table(args.raw_dir, f"{n}.csv")
             for n in ["quiz_responses", "assignments", "answer_key", "participants", "session_process"]}

    wide = method_scores(score_parts(table["quiz_responses"], table["answer_key"]), table["assignments"])
    flags = exclusion_flags(table["participants"], table["session_process"], part_seconds(materials))
    excluded = flags.index[:0] if args.no_exclusions else flags.index[flags.any(axis=1)]
    analysed = wide[~wide.index.isin(excluded)]

    result = paired_tests(analysed["handwritten"], analysed["ai"])
    result = {"n_complete": len(wide), "n_excluded": int(wide.index.isin(excluded).sum()), **result}

    args.results_dir.mkdir(parents=True, exist_ok=True)
    out_name = "paired_ttest_no_exclusions.csv" if args.no_exclusions else "paired_ttest.csv"
    pd.DataFrame([result]).to_csv(args.results_dir / out_name, index=False)

    print(f"{result['n_complete']} complete, {result['n_excluded']} excluded, {result['n_pairs']} analysed")
    if args.no_exclusions:
        print("No exclusions applied (sensitivity run).")
    else:
        print("Exclusions by rule:", flags.sum().to_dict())
    print(f"Mean diff (handwritten - AI) = {result['mean_diff']:.2f} points, "
          f"95% CI [{result['ci95_low']:.2f}, {result['ci95_high']:.2f}]")
    print(f"Paired t({result['df']}) = {result['t']:.3f}, p = {result['p_t']:.4f}, d_z = {result['cohens_dz']:.2f}")
    print(f"Shapiro-Wilk p = {result['shapiro_p']:.4f}; Wilcoxon p = {result['wilcoxon_p']:.4f}, "
          f"r = {result['rank_biserial_r']:.2f}; decision test: {result['decision_test']}")


if __name__ == "__main__":
    main()
