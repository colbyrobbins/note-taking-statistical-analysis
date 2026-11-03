"""This script makes the five figures used in the report and the slides.

Input:  data/processed/scores_wide.csv (from src/clean_data.py)
Output (results/figures/):
    1_power.png           power vs. number of participants, planned (24) and collected (16)
    2_main_result.png     average score with each method, with 95% CIs
    3_who_did_better.png  how many people scored higher with each method
    4_question_type.png   average score by method for each type of question
    5_differences.png     distribution of the paired differences (histogram + Q-Q plot), with Shapiro-Wilk p

Usage:
    python src/make_figures.py
"""
import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy import stats  # noqa: E402

import power_analysis as pa  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
BLUE, ORANGE, GRAY, INK, INK2, GRID = "#2a78d6", "#eb6834", "#a9a7a0", "#1a1a1a", "#55534e", "#e8e7e2"
plt.rcParams.update({"font.size": 12, "axes.titlesize": 14, "axes.titleweight": "bold", "axes.titlelocation": "left",
                     "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2, "axes.edgecolor": "#8a8984",
                     "savefig.dpi": 200, "savefig.facecolor": "white", "figure.facecolor": "white"})


def tidy(ax, grid="y"):
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis=grid, color=GRID, lw=1)
    ax.set_axisbelow(True)


def mean_ci(s: pd.Series) -> tuple[float, float]:
    """Mean and half-width of its 95% t confidence interval."""
    s = s.dropna()
    return s.mean(), stats.t.ppf(0.975, len(s) - 1) * s.std(ddof=1) / np.sqrt(len(s))


def power_figure(n_collected: int, path: Path) -> None:
    ns = np.arange(5, 51)
    fig, ax = plt.subplots(figsize=(8, 4.6))
    ax.plot(ns, [pa.paired_t_power(n, pa.DZ) for n in ns], color=BLUE, lw=3)
    ax.axhline(pa.POWER, color=INK2, lw=1, ls="--")
    ax.text(50, 0.815, "80% power", ha="right", va="bottom", fontsize=11, color=INK2)

    # Mark the planned and the collected sample size; labels sit in the empty space below the curve
    for n, label, color in [(pa.required_n(pa.DZ), "Planned", BLUE), (n_collected, "Collected", ORANGE)]:
        p = pa.paired_t_power(n, pa.DZ)
        ax.plot(n, p, "o", ms=10, color=color, mec="white", mew=2, zorder=3)
        ax.vlines(n, 0, p, color=color, lw=1, ls=":")
        ax.text(n + 1.2, p - 0.13, f"{label}\n{n} people\npower = {p:.2f}", fontsize=11, color=INK, va="top")

    ax.set_xlim(5, 50)
    ax.set_ylim(0, 1.0)
    ax.set_xlabel("Number of participants")
    ax.set_ylabel("Power")
    ax.set_title("How many participants did we need?")
    tidy(ax)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def main_result_figure(wide: pd.DataFrame, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(6.5, 4.6))
    for x, (col, color) in enumerate([("handwritten_score_pct", BLUE), ("ai_score_pct", ORANGE)]):
        m, half = mean_ci(wide[col])
        ax.bar(x, m, width=0.55, color=color)
        ax.errorbar(x, m, yerr=half, color=INK, capsize=6, lw=1.5)
        ax.text(x, m + half + 3, f"{m:.1f}%", ha="center", fontsize=14, fontweight="bold", color=INK)
    ax.set_xticks([0, 1], ["Handwritten notes", "AI summary"])
    ax.set_ylim(0, 110)
    ax.set_yticks(range(0, 101, 20))
    ax.set_ylabel("Average quiz score (% correct)")
    ax.set_title("Average score with each method")
    tidy(ax)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def who_did_better_figure(wide: pd.DataFrame, path: Path) -> None:
    d = wide["diff_score_pct"].round(6)
    counts = [("Better with handwritten notes", int((d > 0).sum()), BLUE),
              ("Same score", int((d == 0).sum()), GRAY),
              ("Better with AI summary", int((d < 0).sum()), ORANGE)]
    fig, ax = plt.subplots(figsize=(7.5, 3.2))
    for y, (label, n, color) in enumerate(counts):
        ax.barh(y, n, height=0.6, color=color)
        ax.text(n + 0.2, y, str(n), va="center", fontsize=13, fontweight="bold", color=INK)
    ax.set_yticks(range(3), [c[0] for c in counts])
    ax.invert_yaxis()
    ax.set_xlim(0, max(c[1] for c in counts) + 2)
    ax.set_xlabel("Number of participants")
    fig.suptitle("Which method gave each person a higher score?", x=0.02, ha="left", fontsize=14, fontweight="bold")
    tidy(ax, grid="x")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def question_type_figure(wide: pd.DataFrame, path: Path) -> None:
    groups = [("Factual", "factual_pct"), ("Conceptual", "conceptual_pct"),
              ("Answer fully\nin the summary", "covered_pct")]
    xs, bw = np.arange(len(groups)), 0.36
    fig, ax = plt.subplots(figsize=(8, 4.6))
    for offset, method, color, name in [(-bw / 2, "handwritten", BLUE, "Handwritten notes"),
                                        (bw / 2, "ai", ORANGE, "AI summary")]:
        values = [wide[f"{method}_{col}"].mean() for _, col in groups]
        ax.bar(xs + offset, values, width=bw, color=color, label=name)
        for x, v in zip(xs + offset, values):
            ax.text(x, v + 1.5, f"{v:.0f}%", ha="center", fontsize=11, color=INK)
    ax.set_xticks(xs, [g for g, _ in groups])
    ax.set_ylim(0, 110)
    ax.set_yticks(range(0, 101, 20))
    ax.set_ylabel("Average score (% correct)")
    ax.set_title("Scores by type of question")
    ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.16), ncols=2)
    tidy(ax)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def difference_distribution_figure(wide: pd.DataFrame, path: Path) -> None:
    """Histogram and normal Q-Q plot of the paired differences the Shapiro-Wilk test checks."""
    d = wide["diff_score_pct"].dropna().to_numpy()
    shapiro_p = stats.shapiro(d).pvalue
    fig, (ax_hist, ax_qq) = plt.subplots(1, 2, figsize=(11, 4.6))

    # Left: scores move in steps of 1/6 (16.7 points), so each bar is one possible difference
    step = 100 / 6
    values, counts = np.unique(np.round(d / step).astype(int), return_counts=True)
    for v, n in zip(values * step, counts):
        ax_hist.bar(v, n, width=step * 0.8, color=BLUE if v > 0 else ORANGE if v < 0 else GRAY)
        ax_hist.text(v, n + 0.15, str(n), ha="center", fontsize=11, fontweight="bold", color=INK)

    # A normal curve with the same mean and SD, scaled to counts, shows what "normal" would look like
    xs = np.linspace(d.min() - 2 * step, d.max() + 2 * step, 200)
    ax_hist.plot(xs, stats.norm.pdf(xs, d.mean(), d.std(ddof=1)) * len(d) * step, color=INK2, lw=1.5, ls="--",
                 label="Normal curve, same mean and SD")
    ax_hist.axvline(0, color=INK2, lw=1)
    ax_hist.legend(frameon=False, loc="upper right", fontsize=10)
    ax_hist.set_xticks(np.arange(-3, 4) * step, [f"{x:+.0f}" if x else "0" for x in np.arange(-3, 4) * step])
    ax_hist.set_xlim(xs.min(), xs.max())
    ax_hist.set_ylim(0, counts.max() + 1.2)
    ax_hist.set_xlabel("Handwritten minus AI score (points)")
    ax_hist.set_ylabel("Number of participants")
    ax_hist.set_title("Score differences")
    tidy(ax_hist)

    # Right: if the differences were normal, the points would sit on the line
    (theoretical, ordered), (slope, intercept, _) = stats.probplot(d, dist="norm")
    ax_qq.plot(theoretical, slope * theoretical + intercept, color=INK2, lw=1.5, ls="--")
    ax_qq.plot(theoretical, ordered, "o", ms=9, color=BLUE, mec="white", mew=2, zorder=3)
    ax_qq.set_xlabel("Expected if normal (z)")
    ax_qq.set_ylabel("Observed difference (points)")
    ax_qq.set_title("Normal Q-Q plot")
    tidy(ax_qq, grid="both")

    fig.suptitle(f"Are the differences normal?  Shapiro-Wilk p = {shapiro_p:.3f}",
                 x=0.02, ha="left", fontsize=14, fontweight="bold")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--processed-dir", type=Path, default=ROOT / "data" / "processed")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "results" / "figures")
    args = parser.parse_args(argv)
    wide = pd.read_csv(args.processed_dir / "scores_wide.csv")
    args.out_dir.mkdir(parents=True, exist_ok=True)

    # We draw each figure from the clean data and save it as a PNG
    power_figure(len(wide), args.out_dir / "1_power.png")
    main_result_figure(wide, args.out_dir / "2_main_result.png")
    who_did_better_figure(wide, args.out_dir / "3_who_did_better.png")
    question_type_figure(wide, args.out_dir / "4_question_type.png")
    difference_distribution_figure(wide, args.out_dir / "5_differences.png")
    print(f"5 figures -> {args.out_dir}")


if __name__ == "__main__":
    main()
