"""Figures for the report and slides.

Usage:
    python src/plots.py

Writes results/figures/paired_scores.png and results/figures/difference_hist.png.
"""
import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from config import DATA_PROCESSED, PRIMARY_TIMEPOINT, RESULTS


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DATA_PROCESSED)
    parser.add_argument("--results-dir", type=Path, default=RESULTS)
    parser.add_argument("--timepoint", default=PRIMARY_TIMEPOINT, choices=["immediate", "delayed"])
    args = parser.parse_args(argv)

    wide = pd.read_csv(args.data_dir / "scores_wide.csv")
    hand = wide[f"handwritten_{args.timepoint}"].to_numpy()
    ai = wide[f"ai_{args.timepoint}"].to_numpy()
    figures = args.results_dir / "figures"
    figures.mkdir(parents=True, exist_ok=True)

    # Paired slope plot: one line per participant
    fig, ax = plt.subplots(figsize=(4.5, 5))
    for h, a in zip(hand, ai):
        ax.plot([0, 1], [h, a], color="gray", alpha=0.4, linewidth=1)
    ax.plot([0, 1], [hand.mean(), ai.mean()], color="black", linewidth=3, marker="o")
    ax.set_xticks([0, 1], ["Handwritten", "AI summary"])
    ax.set_ylabel("Quiz score (% correct)")
    ax.set_title(f"{args.timepoint.capitalize()} quiz, each line = one participant")
    ax.set_xlim(-0.2, 1.2)
    fig.tight_layout()
    fig.savefig(figures / "paired_scores.png", dpi=200)
    plt.close(fig)

    # Histogram of within-person differences
    diff = ai - hand
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.hist(diff, bins=min(12, max(5, len(diff) // 2)), color="steelblue", edgecolor="white")
    ax.axvline(0, color="black", linestyle="--", linewidth=1)
    ax.axvline(np.mean(diff), color="red", linewidth=2, label=f"mean = {np.mean(diff):.1f}")
    ax.set_xlabel("AI minus handwritten (percentage points)")
    ax.set_ylabel("Participants")
    ax.legend()
    fig.tight_layout()
    fig.savefig(figures / "difference_hist.png", dpi=200)
    plt.close(fig)
    print(f"Saved figures to {figures}")


if __name__ == "__main__":
    main()
