"""Generate the counterbalanced assignment schedule.

Participants are assigned to the four sequences in shuffled blocks of four so the
groups stay balanced even if recruitment stops early.

Usage:
    python src/assign_conditions.py --n 30

Writes data/raw/assignments.csv (long format: one row per participant x session).
"""
import argparse
import random
from pathlib import Path

import pandas as pd

from config import DATA_RAW, SEED, SEQUENCES


def build_assignments(n_participants, seed=SEED):
    rng = random.Random(seed)
    seq_ids = list(SEQUENCES)
    order = []
    while len(order) < n_participants:
        block = seq_ids[:]
        rng.shuffle(block)
        order.extend(block)
    order = order[:n_participants]

    rows = []
    for i, seq in enumerate(order, start=1):
        pid = f"P{i:03d}"
        for session_order, (video, method) in enumerate(SEQUENCES[seq], start=1):
            rows.append(
                {
                    "participant_id": pid,
                    "sequence": seq,
                    "session_order": session_order,
                    "video": video,
                    "method": method,
                }
            )
    return pd.DataFrame(rows)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n", type=int, default=30, help="participants to schedule")
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--out", type=Path, default=DATA_RAW / "assignments.csv")
    args = parser.parse_args(argv)

    df = build_assignments(args.n, args.seed)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False)
    print(f"Wrote {len(df)} rows for {args.n} participants to {args.out}")


if __name__ == "__main__":
    main()
