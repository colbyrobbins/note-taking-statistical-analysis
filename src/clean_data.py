"""This script scores the quizzes and builds the clean tables used in the analysis.

Input (data/raw/, written by src/ingest_app_data.py):
    quiz_responses.csv, assignments.csv, answer_key.csv, participants.csv, session_process.csv
Output (data/processed/):
    item_scores.csv   one row per participant x question (correct = 1 or 0)
    scores_long.csv   one row per participant x part: % correct overall, on factual and
                      conceptual questions, and on questions fully covered by the AI summary
    scores_wide.csv   one row per participant: handwritten and AI scores, their difference,
                      predicted scores and background answers

Every participant who completed both parts is kept, and nothing is edited by hand.

Usage:
    python src/clean_data.py
"""
import argparse
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
BACKGROUND = ["age_range", "student_status", "native_english", "device", "usual_note_method",
              "ai_summary_use", "prior_knowledge"]
MEASURES = ["score_pct", "factual_pct", "conceptual_pct", "covered_pct"]


def score_items(quiz: pd.DataFrame, key: pd.DataFrame, assign: pd.DataFrame) -> pd.DataFrame:
    """One row per participant x question, with 1 if the answer matches the key."""
    q_cols = [c for c in quiz.columns if c.startswith("q") and c[1:].isdigit()]
    items = quiz.melt(id_vars=["participant_id", "video"], value_vars=q_cols,
                      var_name="question_id", value_name="answer")
    items = items.merge(key, on=["video", "question_id"], how="left", validate="many_to_one")
    # A missing answer counts as wrong, same as in the app
    items["correct"] = (items["answer"].astype(str).str.strip().str.upper() == items["correct_answer"]).astype(int)
    items = items.merge(assign[["participant_id", "video", "sequence", "method"]],
                        on=["participant_id", "video"], how="left", validate="many_to_one")
    return items.sort_values(["participant_id", "video", "question_id"]).reset_index(drop=True)


def part_scores(items: pd.DataFrame) -> pd.DataFrame:
    """% correct per participant x part, overall and by type of question."""
    def pct(g, mask=None):
        g = g if mask is None else g[mask]
        return 100 * g["correct"].mean() if len(g) else float("nan")

    rows = []
    for (pid, video, seq, method), g in items.groupby(["participant_id", "video", "sequence", "method"]):
        rows.append({"participant_id": pid, "video": video, "sequence": seq, "method": method,
                     "n_correct": int(g["correct"].sum()),
                     "score_pct": pct(g),
                     "factual_pct": pct(g, g["question_type"] == "factual"),
                     "conceptual_pct": pct(g, g["question_type"] == "conceptual"),
                     "covered_pct": pct(g, g["summary_coverage"] == "full")})
    return pd.DataFrame(rows)


def to_wide(long: pd.DataFrame, participants: pd.DataFrame, process: pd.DataFrame) -> pd.DataFrame:
    """One row per person: each score under each method, and handwritten minus AI."""
    wide = long.pivot(index="participant_id", columns="method", values=MEASURES)
    wide.columns = [f"{method}_{m}" for m, method in wide.columns]
    for m in MEASURES:
        wide[f"diff_{m}"] = wide[f"handwritten_{m}"] - wide[f"ai_{m}"]

    # We also keep the score each person predicted (0-6), as a % so it compares with the real score
    pred = process.assign(predicted_pct=100 * pd.to_numeric(process["predicted_correct"], errors="coerce") / 6)
    pred = pred.pivot(index="participant_id", columns="method", values="predicted_pct")
    wide = wide.join(pred.add_suffix("_predicted_pct")).reset_index()
    return participants[["participant_id", "sequence", *BACKGROUND]].merge(wide, on="participant_id")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--raw-dir", type=Path, default=ROOT / "data" / "raw")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "data" / "processed")
    args = parser.parse_args(argv)

    # First we read the tables written by the ingest script
    raw = args.raw_dir
    quiz = pd.read_csv(raw / "quiz_responses.csv", dtype=str)
    assign = pd.read_csv(raw / "assignments.csv", dtype=str)
    key = pd.read_csv(raw / "answer_key.csv")
    participants = pd.read_csv(raw / "participants.csv", dtype=str)
    process = pd.read_csv(raw / "session_process.csv", dtype=str)

    # Then we score every answer and roll the questions up into part scores
    items = score_items(quiz, key, assign)
    long = part_scores(items)
    wide = to_wide(long, participants, process)

    # Finally we save the three clean tables
    args.out_dir.mkdir(parents=True, exist_ok=True)
    items.to_csv(args.out_dir / "item_scores.csv", index=False)
    long.to_csv(args.out_dir / "scores_long.csv", index=False)
    wide.to_csv(args.out_dir / "scores_wide.csv", index=False)
    print(f"{len(wide)} participants scored -> {args.out_dir}")


if __name__ == "__main__":
    main()
