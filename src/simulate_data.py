"""Generate SIMULATED data in the raw Google Forms format.

This exists only to test the cleaning/analysis pipeline before real data arrives.
Never report simulated results as findings.

Usage:
    python src/simulate_data.py --n 30 --effect 0.3 --out-dir data/simulated
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from assign_conditions import build_assignments
from config import DATA_SIMULATED, SEED

N_FACTUAL = 5
N_CONCEPTUAL = 5
CHOICES = list("ABCD")


def build_answer_key(rng):
    rows = []
    for video in ("A", "B"):
        for i in range(1, N_FACTUAL + N_CONCEPTUAL + 1):
            rows.append(
                {
                    "video": video,
                    "question_id": f"q{i:02d}",
                    "question_type": "factual" if i <= N_FACTUAL else "conceptual",
                    "correct_answer": rng.choice(CHOICES),
                }
            )
    return pd.DataFrame(rows)


def simulate(n, effect, dropout, seed):
    """effect = shift in log-odds of a correct answer for AI vs handwritten notes."""
    rng = np.random.default_rng(seed)
    assign = build_assignments(n, seed)
    key = build_answer_key(rng)
    ability = {pid: rng.normal(0, 0.8) for pid in assign["participant_id"].unique()}
    dropped = {pid for pid in ability if rng.random() < dropout}

    rows = []
    for _, a in assign.iterrows():
        for timepoint in ("immediate", "delayed"):
            if timepoint == "delayed" and a["participant_id"] in dropped:
                continue
            logit = (
                0.8
                + ability[a["participant_id"]]
                + (effect if a["method"] == "ai" else 0.0)
                + (-0.5 if timepoint == "delayed" else 0.0)
            )
            p_correct = 1 / (1 + np.exp(-logit))
            row = {"participant_id": a["participant_id"], "video": a["video"], "timepoint": timepoint}
            for _, k in key[key["video"] == a["video"]].iterrows():
                if rng.random() < p_correct:
                    row[k["question_id"]] = k["correct_answer"]
                else:
                    row[k["question_id"]] = rng.choice([c for c in CHOICES if c != k["correct_answer"]])
            rows.append(row)
    return pd.DataFrame(rows), key, assign


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n", type=int, default=30)
    parser.add_argument("--effect", type=float, default=0.3, help="log-odds boost for AI notes")
    parser.add_argument("--dropout", type=float, default=0.1)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--out-dir", type=Path, default=DATA_SIMULATED)
    args = parser.parse_args(argv)

    responses, key, assign = simulate(args.n, args.effect, args.dropout, args.seed)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    responses.to_csv(args.out_dir / "quiz_responses.csv", index=False)
    key.to_csv(args.out_dir / "answer_key.csv", index=False)
    assign.to_csv(args.out_dir / "assignments.csv", index=False)
    print(f"Wrote simulated data for {args.n} participants to {args.out_dir}")


if __name__ == "__main__":
    main()
