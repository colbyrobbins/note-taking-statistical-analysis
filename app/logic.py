"""Pure study logic for the data-collection app (no Streamlit imports, so it is unit-testable).

Design (see docs/protocol.md):
    One video split into two halves, A (Part 1) and B (Part 2), always watched in that order.
    Each participant uses one note-taking method per half; the method order is counterbalanced:
        sequence 1: Part 1 handwritten, Part 2 AI summary
        sequence 2: Part 1 AI summary,  Part 2 handwritten
    New participants are allocated to whichever sequence has fewer *completed* (non-pilot)
    participants, with random tie-breaking, so the two sequences stay balanced in the
    final sample even when some people quit halfway.
"""
from __future__ import annotations

import json
import random
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MATERIALS_PATH = ROOT / "materials" / "study_materials.json"

APP_VERSION = "1.0.0"
PARTS = ("A", "B")
METHODS = ("handwritten", "ai")
SEQUENCES = {
    1: {"A": "handwritten", "B": "ai"},
    2: {"A": "ai", "B": "handwritten"},
}
REVIEW_MAX_SECONDS = 120
PLACEHOLDER_PREFIX = "PASTE_CHATGPT_SUMMARY"

BACKGROUND_FIELDS = [
    "student_status",
    "native_english",
    "usual_note_method",
    "ai_summary_use",
    "prior_knowledge",
    "attention_check",
]
ATTENTION_CORRECT = "Often"


def part_fields(part: str, n_questions: int = 6) -> list[str]:
    p = "p1" if part == "A" else "p2"
    return (
        [f"{p}_method", f"{p}_watch_seconds", f"{p}_review_seconds", f"{p}_review_timed_out", f"{p}_quiz_seconds"]
        + [f"{p}_q{i:02d}" for i in range(1, n_questions + 1)]
        + [f"{p}_predicted_correct", f"{p}_compliance", f"{p}_used_material_during_quiz"]
    )


FIELDNAMES = (
    ["participant_id", "is_pilot", "app_version", "sequence", "started_at", "completed_at"]
    + BACKGROUND_FIELDS
    + part_fields("A")
    + part_fields("B")
)


def load_materials(path: Path = MATERIALS_PATH) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def summaries_missing(materials: dict) -> list[str]:
    """Labels of parts whose ChatGPT summary has not been pasted in yet."""
    return [
        materials["parts"][p]["label"]
        for p in PARTS
        if str(materials["parts"][p]["ai_summary"]).startswith(PLACEHOLDER_PREFIX)
    ]


def make_participant_id() -> str:
    """Random pseudonymous ID, e.g. P-3F9A1C2B. Contains no personal information."""
    return "P-" + uuid.uuid4().hex[:8].upper()


def choose_sequence(completed_sequences: list[int], rng: random.Random | None = None) -> int:
    """Pick the sequence with the fewest completed participants (ties broken at random)."""
    rng = rng or random.Random()
    counts = {s: 0 for s in SEQUENCES}
    for s in completed_sequences:
        if s in counts:
            counts[s] += 1
    fewest = min(counts.values())
    return rng.choice(sorted(s for s, c in counts.items() if c == fewest))


def score_part(answers: dict[str, str | None], questions: list[dict]) -> int:
    """Number of correct answers for one part (unanswered counts as incorrect)."""
    return sum(1 for q in questions if answers.get(q["id"]) == q["answer"])


def empty_record() -> dict:
    return {k: "" for k in FIELDNAMES}
