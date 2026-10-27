"""Convert the app's export (one row per participant) into the raw files the pipeline reads.

Input:  data/raw/app_responses.csv  (download the Google Sheet as CSV; never edit it by hand)
Output (in --out-dir, default data/raw/):
    quiz_responses.csv   participant x part: participant_id, video (A/B), timepoint, q01..q06
    assignments.csv      participant x part: participant_id, sequence, session_order, video, method
    answer_key.csv       video, question_id, question_type, correct_answer (from materials/)
    participants.csv     one row per participant: background answers incl. exclusion fields
    session_process.csv  participant x part: watch/review/quiz seconds, predicted score, compliance
Pilot rows (is_pilot = True) are written to data/pilot/app_responses_pilot.csv and excluded.

Part 1 of the video is "A" and Part 2 is "B"; Part 1 is always watched first.

Usage:
    python src/ingest_app_data.py
"""
import argparse
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = ROOT / "data" / "raw"

MATERIALS = ROOT / "materials" / "study_materials.json"
BACKGROUND = ["student_status", "native_english", "usual_note_method", "ai_summary_use",
              "prior_knowledge", "attention_check"]
PROCESS = ["method", "watch_seconds", "review_seconds", "review_timed_out", "quiz_seconds",
           "predicted_correct", "compliance", "used_material_during_quiz"]
PARTS = {"A": ("p1", 1), "B": ("p2", 2)}


def answer_key(materials: dict) -> pd.DataFrame:
    rows = [
        {"video": part, "question_id": q["id"], "question_type": q["type"], "correct_answer": q["answer"],
         # does the AI summary of this part contain the answer? (full / partial / none) -> robustness check
         "summary_coverage": q.get("summary_coverage", "")}
        for part, qs in materials["questions"].items()
        for q in qs
    ]
    return pd.DataFrame(rows)


def split_pilot(app: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    is_pilot = app["is_pilot"].astype(str).str.strip().str.lower().isin(["true", "1", "yes"])
    return app[~is_pilot].copy(), app[is_pilot].copy()


def to_raw_tables(app: pd.DataFrame, n_questions: int) -> dict[str, pd.DataFrame]:
    quiz, assign, process = [], [], []
    for _, r in app.iterrows():
        for video, (p, order) in PARTS.items():
            quiz.append({"participant_id": r["participant_id"], "video": video, "timepoint": "immediate",
                         **{f"q{i:02d}": r.get(f"{p}_q{i:02d}") for i in range(1, n_questions + 1)}})
            assign.append({"participant_id": r["participant_id"], "sequence": r["sequence"],
                           "session_order": order, "video": video, "method": r[f"{p}_method"]})
            process.append({"participant_id": r["participant_id"], "video": video, "session_order": order,
                            **{k: r.get(f"{p}_{k}") for k in PROCESS}})
    participants = app[["participant_id", "sequence", "started_at", "completed_at", *BACKGROUND]].copy()
    return {
        "quiz_responses.csv": pd.DataFrame(quiz),
        "assignments.csv": pd.DataFrame(assign),
        "session_process.csv": pd.DataFrame(process),
        "participants.csv": participants,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app-file", type=Path, default=DATA_RAW / "app_responses.csv")
    parser.add_argument("--out-dir", type=Path, default=DATA_RAW)
    parser.add_argument("--pilot-dir", type=Path, default=ROOT / "data" / "pilot")
    args = parser.parse_args(argv)

    materials = json.loads(MATERIALS.read_text(encoding="utf-8"))
    n_questions = len(materials["questions"]["A"])
    app = pd.read_csv(args.app_file, dtype=str)

    dupes = app.duplicated("participant_id", keep="first")
    if dupes.any():
        print(f"Dropping {int(dupes.sum())} duplicate participant row(s) (kept first).")
        app = app[~dupes]

    real, pilot = split_pilot(app)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    if len(pilot):
        args.pilot_dir.mkdir(parents=True, exist_ok=True)
        pilot.to_csv(args.pilot_dir / "app_responses_pilot.csv", index=False)

    for name, df in to_raw_tables(real, n_questions).items():
        df.to_csv(args.out_dir / name, index=False)
    answer_key(materials).to_csv(args.out_dir / "answer_key.csv", index=False)
    print(f"{len(real)} participants ingested ({len(pilot)} pilot rows set aside) -> {args.out_dir}")


if __name__ == "__main__":
    main()
