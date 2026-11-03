"""This script turns the app's export into the raw tables the analysis uses.

The app saves one row per participant to a Google Sheet. We download it as CSV, keep the columns
the analysis uses, save it as data/raw/app_responses.csv, and this script reshapes it into one row
per participant and part.

Input:  data/raw/app_responses.csv
Output (data/raw/):
    quiz_responses.csv   participant x part: the answer chosen for each of the 6 questions
    assignments.csv      participant x part: sequence, order and method (handwritten or ai)
    answer_key.csv       correct answer, question type and summary coverage for every question
    participants.csv     one row per participant: background answers
    session_process.csv  participant x part: the score each person predicted after the quiz
Pilot rows (is_pilot = True) are saved to data/pilot/ and left out.

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

BACKGROUND = ["age_range", "student_status", "native_english", "device", "usual_note_method",
              "ai_summary_use", "prior_knowledge"]
PROCESS = ["method", "predicted_correct"]
PARTS = {"A": ("p1", 1), "B": ("p2", 2)}  # Part 1 of the video is "A", Part 2 is "B"


def answer_key(materials: dict) -> pd.DataFrame:
    """One row per question, taken from the study materials."""
    rows = [
        {"video": part, "question_id": q["id"], "question_type": q["type"], "correct_answer": q["answer"],
         # does the AI summary of this part contain the answer? (full / partial / none)
         "summary_coverage": q.get("summary_coverage", "")}
        for part, qs in materials["questions"].items()
        for q in qs
    ]
    return pd.DataFrame(rows)


def split_pilot(app: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Separate real participants from pilot sessions."""
    is_pilot = app["is_pilot"].astype(str).str.strip().str.lower().isin(["true", "1", "yes"])
    return app[~is_pilot].copy(), app[is_pilot].copy()


def to_raw_tables(app: pd.DataFrame, n_questions: int) -> dict[str, pd.DataFrame]:
    """Reshape one row per participant into one row per participant and part."""
    quiz, assign, process = [], [], []
    for _, r in app.iterrows():
        for video, (p, order) in PARTS.items():
            quiz.append({"participant_id": r["participant_id"], "video": video,
                         **{f"q{i:02d}": r.get(f"{p}_q{i:02d}") for i in range(1, n_questions + 1)}})
            assign.append({"participant_id": r["participant_id"], "sequence": r["sequence"],
                           "session_order": order, "video": video, "method": r[f"{p}_method"]})
            process.append({"participant_id": r["participant_id"], "video": video, "session_order": order,
                            **{k: r.get(f"{p}_{k}") for k in PROCESS}})
    participants = app[["participant_id", "sequence", *BACKGROUND]].copy()
    return {
        "quiz_responses.csv": pd.DataFrame(quiz),
        "assignments.csv": pd.DataFrame(assign),
        "session_process.csv": pd.DataFrame(process),
        "participants.csv": participants,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--app-file", type=Path, default=DATA_RAW / "app_responses.csv")
    parser.add_argument("--out-dir", type=Path, default=DATA_RAW)
    parser.add_argument("--pilot-dir", type=Path, default=ROOT / "data" / "pilot")
    args = parser.parse_args(argv)

    # First we load the export and the quiz questions
    materials = json.loads(MATERIALS.read_text(encoding="utf-8"))
    n_questions = len(materials["questions"]["A"])
    app = pd.read_csv(args.app_file, dtype=str)

    # We keep only the first row if someone appears twice
    dupes = app.duplicated("participant_id", keep="first")
    if dupes.any():
        print(f"Dropping {int(dupes.sum())} duplicate participant row(s) (kept first).")
        app = app[~dupes]

    # Then we set pilot sessions aside so they never reach the analysis
    real, pilot = split_pilot(app)
    if len(pilot):
        args.pilot_dir.mkdir(parents=True, exist_ok=True)
        pilot.to_csv(args.pilot_dir / "app_responses_pilot.csv", index=False)

    # Finally we write the tables
    args.out_dir.mkdir(parents=True, exist_ok=True)
    for name, df in to_raw_tables(real, n_questions).items():
        df.to_csv(args.out_dir / name, index=False)
    answer_key(materials).to_csv(args.out_dir / "answer_key.csv", index=False)
    print(f"{len(real)} participants ingested ({len(pilot)} pilot rows set aside) -> {args.out_dir}")


if __name__ == "__main__":
    main()
