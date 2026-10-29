"""A priori power analysis for the paired t-test.

Each participant is tested under both methods, so we compare their two quiz scores with a
two-tailed paired t-test. The effect size for this design is Cohen's d_z: the mean of the
paired differences divided by their standard deviation.

Assumptions:
    d_z = 0.6     the smallest effect we want to be able to detect (medium)
    alpha = 0.05  two-tailed, since the AI summary could help or hurt
    power = 0.80

Power is computed exactly from the noncentral t distribution (same method as G*Power,
"Means: difference between two dependent means").

Outputs:
    results/power_required_n.csv      participants needed for a range of effect sizes
    results/power_sensitivity.csv     power and smallest detectable effect at the n we may reach
    results/figures/power_curve.png   power vs. sample size

Usage:
    python src/power_analysis.py
"""
import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy import optimize, stats  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]

DZ = 0.6
ALPHA = 0.05
POWER = 0.80
TARGET_N = 30  # 24 plus room for about 20% exclusions


def paired_t_power(n: int, dz: float, alpha: float = ALPHA) -> float:
    """Power of a two-tailed paired t-test with n pairs."""
    df = n - 1
    noncentrality = dz * np.sqrt(n)
    t_crit = stats.t.ppf(1 - alpha / 2, df)
    # Power is the chance the t statistic lands beyond either critical value.
    # The lower tail is tiny for any real effect and scipy can return NaN when it underflows.
    upper = stats.nct.sf(t_crit, df, noncentrality)
    lower = np.nan_to_num(stats.nct.cdf(-t_crit, df, noncentrality), nan=0.0)
    return float(upper + lower)


def required_n(dz: float, alpha: float = ALPHA, power: float = POWER) -> int:
    """Smallest number of pairs that reaches the target power."""
    n = 3
    while paired_t_power(n, dz, alpha) < power:
        n += 1
    return n


def detectable_dz(n: int, alpha: float = ALPHA, power: float = POWER) -> float:
    """Smallest d_z that n pairs can detect with the target power."""
    return float(optimize.brentq(lambda d: paired_t_power(n, d, alpha) - power, 0.05, 1.5))


def plot_power_curve(path: Path) -> None:
    ns = np.arange(5, 61)
    fig, ax = plt.subplots(figsize=(7, 4.2), dpi=200)

    # Our planned effect in color, a smaller and a larger one in gray for context
    # Each curve is labeled where it crosses n = 12, where the three are well apart
    for dz, color, width in [(0.4, "#b8b6b0", 1.6), (0.8, "#b8b6b0", 1.6), (DZ, "#2a78d6", 2.4)]:
        power = [paired_t_power(n, dz) for n in ns]
        ax.plot(ns, power, color=color, lw=width, solid_capstyle="round")
        ax.text(12.6, paired_t_power(12, dz) - 0.015, f"$d_z$ = {dz}", va="top", fontsize=9,
                color="#0b0b0b" if dz == DZ else "#52514e")

    n_needed = required_n(DZ)
    ax.axhline(POWER, color="#52514e", lw=0.8, ls=(0, (3, 3)))
    ax.plot([n_needed], [paired_t_power(n_needed, DZ)], "o", ms=7, color="#2a78d6", mec="white", mew=2)
    ax.annotate(f"n = {n_needed} for 80% power", (n_needed, paired_t_power(n_needed, DZ)),
                xytext=(n_needed + 3, 0.55), fontsize=9, color="#0b0b0b",
                arrowprops=dict(arrowstyle="-", color="#52514e", lw=0.8))

    ax.set_xlim(5, 60)
    ax.set_ylim(0, 1.02)
    ax.set_xlabel("Participants (complete pairs)")
    ax.set_ylabel("Power")
    ax.set_title("Power of a two-tailed paired t-test (alpha = 0.05)", loc="left", fontsize=11)
    _clean_axes(ax)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, facecolor="white")
    plt.close(fig)


def _clean_axes(ax) -> None:
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color("#8a8984")
    ax.tick_params(colors="#52514e", labelsize=9)
    ax.grid(axis="y", color="#e6e5e0", lw=0.8)
    ax.set_axisbelow(True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--results-dir", type=Path, default=ROOT / "results")
    args = parser.parse_args(argv)
    args.results_dir.mkdir(parents=True, exist_ok=True)

    # First, how many people do we need for different effect sizes?
    # 0.25 is roughly the handwritten vs. typed effect in the literature (Flanigan et al., 2024).
    required = pd.DataFrame({"d_z": [0.25, 0.4, 0.5, 0.6, 0.8]})
    required["required_n"] = required["d_z"].apply(required_n)
    required["achieved_power"] = [round(paired_t_power(n, d), 3)
                                  for n, d in zip(required["required_n"], required["d_z"])]
    required.to_csv(args.results_dir / "power_required_n.csv", index=False)

    # Then, what can we detect with the sample sizes we might actually end up with?
    sensitivity = pd.DataFrame({"n": [20, 24, TARGET_N, 36]})
    sensitivity[f"power_at_dz_{DZ}"] = sensitivity["n"].apply(lambda n: round(paired_t_power(n, DZ), 3))
    sensitivity["min_detectable_dz"] = sensitivity["n"].apply(lambda n: round(detectable_dz(n), 3))
    sensitivity.to_csv(args.results_dir / "power_sensitivity.csv", index=False)

    plot_power_curve(args.results_dir / "figures" / "power_curve.png")

    n_needed = required_n(DZ)
    print(f"Paired t-test, d_z = {DZ}, alpha = {ALPHA} (two-tailed), power = {POWER:.0%}: "
          f"n = {n_needed} (achieved power {paired_t_power(n_needed, DZ):.3f}).")
    print(f"Target n = {TARGET_N}: power {paired_t_power(TARGET_N, DZ):.3f}, "
          f"smallest detectable d_z {detectable_dz(TARGET_N):.2f}.")


if __name__ == "__main__":
    main()
