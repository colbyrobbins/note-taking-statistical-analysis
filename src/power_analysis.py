"""A-priori power analysis for the two-tailed paired t-test.

Usage:
    python src/power_analysis.py

Writes results/tables/power_analysis.csv and results/figures/power_curve.png.
"""
import argparse
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from config import ALPHA, EXPECTED_DROPOUT, EXPECTED_EFFECT_DZ, RESULTS, TARGET_POWER


def paired_t_power(effect_size, n, alpha=ALPHA):
    """Exact power of a two-tailed paired t-test via the noncentral t distribution.

    effect_size is d_z (mean difference / SD of differences); n is the number of pairs.
    """
    df = n - 1
    nc = effect_size * math.sqrt(n)
    t_crit = stats.t.ppf(1 - alpha / 2, df)
    return stats.nct.sf(t_crit, df, nc) + stats.nct.cdf(-t_crit, df, nc)


def required_n(effect_size, alpha=ALPHA, power=TARGET_POWER):
    """Smallest whole number of pairs reaching the target power."""
    n = 3
    while paired_t_power(effect_size, n, alpha) < power:
        n += 1
    return n


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path, default=RESULTS)
    args = parser.parse_args(argv)

    tables = args.results_dir / "tables"
    figures = args.results_dir / "figures"
    tables.mkdir(parents=True, exist_ok=True)
    figures.mkdir(parents=True, exist_ok=True)

    n_main = required_n(EXPECTED_EFFECT_DZ)
    n_recruit = math.ceil(n_main / (1 - EXPECTED_DROPOUT))
    print(f"d_z={EXPECTED_EFFECT_DZ}, alpha={ALPHA} (two-tailed), power={TARGET_POWER}")
    print(f"Required complete pairs: {n_main}")
    print(f"Recruit {n_recruit} to allow for {EXPECTED_DROPOUT:.0%} dropout")

    # Sensitivity: required n across plausible effect sizes
    rows = [
        {"d_z": d, "n_pairs": required_n(d), "n_to_recruit": math.ceil(required_n(d) / (1 - EXPECTED_DROPOUT))}
        for d in (0.4, 0.5, 0.6, 0.7, 0.8)
    ]
    pd.DataFrame(rows).to_csv(tables / "power_analysis.csv", index=False)

    # Power curve
    ns = np.arange(5, 61)
    fig, ax = plt.subplots(figsize=(6, 4))
    for d in (0.4, 0.6, 0.8):
        power = [paired_t_power(d, n) for n in ns]
        ax.plot(ns, power, label=f"d_z = {d}")
    ax.axhline(TARGET_POWER, color="gray", linestyle="--", linewidth=1)
    ax.axvline(n_main, color="gray", linestyle=":", linewidth=1)
    ax.set_xlabel("Number of participants (pairs)")
    ax.set_ylabel("Power")
    ax.set_title("Power of two-tailed paired t-test (alpha = 0.05)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(figures / "power_curve.png", dpi=200)
    plt.close(fig)


if __name__ == "__main__":
    main()
