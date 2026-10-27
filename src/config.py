"""Shared constants and paths for the note-taking experiment.

Everything that defines the study design (alpha, target power, expected effect,
counterbalancing sequences) lives here so the power analysis, assignment, and
analysis scripts cannot drift apart.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"
DATA_SIMULATED = ROOT / "data" / "simulated"
RESULTS = ROOT / "results"

# --- Statistical design -----------------------------------------------------
ALPHA = 0.05                 # two-tailed
TARGET_POWER = 0.80
EXPECTED_EFFECT_DZ = 0.6     # paired Cohen's d (d_z); ASSUMPTION, see docs/protocol.md
EXPECTED_DROPOUT = 0.15      # share who skip the 48-hour quiz; ASSUMPTION
SEED = 510

# --- Experimental design ----------------------------------------------------
METHODS = ("handwritten", "ai")
VIDEOS = ("A", "B")
TIMEPOINTS = ("immediate", "delayed")
PRIMARY_TIMEPOINT = "delayed"          # the single confirmatory t-test
SECONDARY_TIMEPOINT = "immediate"      # exploratory

# Counterbalancing: each participant watches both videos and uses both methods.
# Each sequence lists (video, method) in viewing order. Crossing video order with
# method order means neither video difficulty nor practice effects line up with
# one method.
SEQUENCES = {
    1: (("A", "handwritten"), ("B", "ai")),
    2: (("A", "ai"), ("B", "handwritten")),
    3: (("B", "handwritten"), ("A", "ai")),
    4: (("B", "ai"), ("A", "handwritten")),
}
