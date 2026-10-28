"""Pure study logic for the data-collection app (no Streamlit imports, so it is unit-testable).

Design (see docs/protocol.md):
    One video split into two halves, A (Part 1) and B (Part 2), always watched in that order.
    Each participant uses one note-taking method per half; the method order is counterbalanced:
        sequence 1: Part 1 handwritten, Part 2 AI summary
        sequence 2: Part 1 AI summary,  Part 2 handwritten
    New participants are allocated with Efron's biased coin (Efron, 1971), counting every
    (non-pilot) participant who has *started* (each start is logged before Part 1): if one
    sequence has fewer starts, it is chosen with probability 2/3; if they are tied, 1/2. This keeps the final sample close to balanced even when
    some people quit halfway, while staying random, so that many participants starting at the
    same moment (e.g. a class session) are not all pushed into the same sequence.
"""
from __future__ import annotations

import json
import random
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MATERIALS_PATH = ROOT / "materials" / "study_materials.json"

APP_VERSION = "1.1.0"
PARTS = ("A", "B")
METHODS = ("handwritten", "ai")
SEQUENCES = {
    1: {"A": "handwritten", "B": "ai"},
    2: {"A": "ai", "B": "handwritten"},
}
REVIEW_MAX_SECONDS = 120
EFRON_P = 2 / 3
PLACEHOLDER_PREFIX = "PASTE_CHATGPT_SUMMARY"

BACKGROUND_FIELDS = [
    "taken_before_or_seen_video",
    "age_range",
    "student_status",
    "native_english",
    "device",
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
        + [f"{p}_predicted_correct", f"{p}_compliance", f"{p}_ai_part_wrote_notes",
           f"{p}_paused_or_rewound", f"{p}_used_material_during_quiz"]
    )


ALLOCATION_FIELDS = ["participant_id", "is_pilot", "app_version", "sequence", "started_at"]

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


def choose_sequence(started_sequences: list[int], rng: random.Random | None = None) -> int:
    """Efron's biased coin: favor the sequence with fewer started participants (p = 2/3)."""
    rng = rng or random.Random()
    counts = {s: 0 for s in SEQUENCES}
    for s in started_sequences:
        if s in counts:
            counts[s] += 1
    (s1, c1), (s2, c2) = sorted(counts.items())
    if c1 == c2:
        return rng.choice([s1, s2])
    behind, ahead = (s1, s2) if c1 < c2 else (s2, s1)
    return behind if rng.random() < EFRON_P else ahead


def score_part(answers: dict[str, str | None], questions: list[dict]) -> int:
    """Number of correct answers for one part (unanswered counts as incorrect)."""
    return sum(1 for q in questions if answers.get(q["id"]) == q["answer"])


def empty_record() -> dict:
    return {k: "" for k in FIELDNAMES}
