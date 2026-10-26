"""Clean and score raw Google Forms exports.

Expected files in --raw-dir (see docs/data_dictionary.md):
    quiz_responses.csv  participant_id, video, timepoint, [timestamp], q01..qNN
    answer_key.csv      video, question_id, question_type, correct_answer
    assignments.csv     participant_id, sequence, session_order, video, method

Usage:
    python src/clean_data.py

Writes to --out-dir:
    scores_long.csv   one row per participant x video x timepoint
    scores_wide.csv   one row per participant with all four method x timepoint scores
and results/tables/exclusions.csv listing participants dropped for missing data.
"""
import argparse
import re
from pathlib import Path

import pandas as pd

from config import DATA_PROCESSED, DATA_RAW, METHODS, RESULTS, TIMEPOINTS


def load_raw(raw_dir):
    responses = pd.read_csv(raw_dir / "quiz_responses.csv", dtype=str)
    key = pd.read_csv(raw_dir / "answer_key.csv", dtype=str)
    assign = pd.read_csv(raw_dir / "assignments.csv", dtype=str)
    return responses, key, assign


def normalise(responses, key, assign):
    for df in (responses, key, assign):
        df.columns = [c.strip().lower() for c in df.columns]
    responses["participant_id"] = responses["participant_id"].str.strip().str.upper()
    assign["participant_id"] = assign["participant_id"].str.strip().str.upper()
    for df in (responses, key, assign):
        df["video"] = df["video"].str.strip().str.upper()
    responses["timepoint"] = responses["timepoint"].str.strip().str.lower()
    assign["method"] = assign["method"].str.strip().str.lower()
    key["question_id"] = key["question_id"].str.strip().str.lower()
    key["question_type"] = key["question_type"].str.strip().str.lower()
    key["correct_answer"] = key["correct_answer"].str.strip().str.upper()
    return responses, key, assign


def drop_duplicate_submissions(responses):
    """Keep each participant's first submission per video x timepoint."""
    keys = ["participant_id", "video", "timepoint"]
    if "timestamp" in responses.columns:
        responses = responses.assign(_ts=pd.to_datetime(responses["timestamp"], errors="coerce"))
        responses = responses.sort_values("_ts").drop(columns="_ts")
    n_before = len(responses)
    responses = responses.drop_duplicates(subset=keys, keep="first")
    return responses, n_before - len(responses)


def score(responses, key):
    qcols = [c for c in responses.columns if re.fullmatch(r"q\d+", c)]
    long = responses.melt(
        id_vars=["participant_id", "video", "timepoint"],
        value_vars=qcols,
        var_name="question_id",
        value_name="answer",
    )
    long = long.merge(key, on=["video", "question_id"], how="inner")
    # Unanswered questions (NaN) compare False, i.e. count as incorrect.
    long["correct"] = (long["answer"].str.strip().str.upper() == long["correct_answer"]).astype(int)

    group = ["participant_id", "video", "timepoint"]
    totals = long.groupby(group)["correct"].agg(n_questions="size", n_correct="sum").reset_index()
    totals["pct_total"] = 100 * totals["n_correct"] / totals["n_questions"]
    for qtype in ("factual", "conceptual"):
        sub = long[long["question_type"] == qtype].groupby(group)["correct"].mean() * 100
        totals = totals.merge(sub.rename(f"pct_{qtype}").reset_index(), on=group, how="left")
    return totals


def make_wide(scores_long, assign):
    first = assign[assign["session_order"] == "1"][["participant_id", "method"]].rename(
        columns={"method": "first_method"}
    )
    wide = scores_long.pivot_table(
        index="participant_id", columns=["method", "timepoint"], values="pct_total"
    )
    expected = [(m, t) for m in METHODS for t in TIMEPOINTS]
    wide = wide.reindex(columns=pd.MultiIndex.from_tuples(expected))
    wide.columns = [f"{m}_{t}" for m, t in wide.columns]
    wide = wide.reset_index()
    seq = assign[["participant_id", "sequence"]].drop_duplicates()
    return wide.merge(seq, on="participant_id", how="left").merge(first, on="participant_id", how="left")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=DATA_RAW)
    parser.add_argument("--out-dir", type=Path, default=DATA_PROCESSED)
    parser.add_argument("--results-dir", type=Path, default=RESULTS)
    args = parser.parse_args(argv)

    responses, key, assign = normalise(*load_raw(args.raw_dir))
    responses, n_dupes = drop_duplicate_submissions(responses)
    if n_dupes:
        print(f"Dropped {n_dupes} duplicate submission(s) (kept first).")

    scores = score(responses, key)
    scores = scores.merge(
        assign[["participant_id", "video", "method", "sequence"]],
        on=["participant_id", "video"],
        how="left",
    )
    unmatched = scores["method"].isna().sum()
    if unmatched:
        raise ValueError(f"{unmatched} score rows have no matching assignment; check IDs/videos.")

    wide = make_wide(scores, assign)
    score_cols = [f"{m}_{t}" for m in METHODS for t in TIMEPOINTS]
    complete = wide.dropna(subset=score_cols)
    excluded = wide[wide[score_cols].isna().any(axis=1)].copy()
    excluded["missing"] = excluded[score_cols].isna().apply(
        lambda r: ", ".join(c for c in score_cols if r[c]), axis=1
    )
    # Participants who were scheduled but never submitted anything
    never = sorted(set(assign["participant_id"]) - set(wide["participant_id"]))
    never_df = pd.DataFrame({"participant_id": never, "missing": "all"})

    args.out_dir.mkdir(parents=True, exist_ok=True)
    tables = args.results_dir / "tables"
    tables.mkdir(parents=True, exist_ok=True)
    scores.to_csv(args.out_dir / "scores_long.csv", index=False)
    complete.to_csv(args.out_dir / "scores_wide.csv", index=False)
    pd.concat([excluded[["participant_id", "missing"]], never_df]).to_csv(
        tables / "exclusions.csv", index=False
    )
    print(
        f"{len(complete)} complete participants kept; "
        f"{len(excluded) + len(never)} excluded (see {tables / 'exclusions.csv'})."
    )


if __name__ == "__main__":
    main()
