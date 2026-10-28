import random
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))
sys.path.insert(0, str(ROOT / "src"))

import ingest_app_data  # noqa: E402
import logic  # noqa: E402


def test_allocation_keeps_sequences_balanced():
    rng = random.Random(0)
    completed = []
    for _ in range(31):
        completed.append(logic.choose_sequence(completed, rng))
    counts = pd.Series(completed).value_counts()
    assert counts.max() - counts.min() <= 1


def test_allocation_ignores_unknown_sequences():
    assert logic.choose_sequence([1, 1, 1, 99], random.Random(0)) == 2


def test_every_sequence_uses_both_methods_once():
    for seq in logic.SEQUENCES.values():
        assert sorted(seq.values()) == sorted(logic.METHODS)


def test_materials_are_well_formed():
    m = logic.load_materials()
    for part in logic.PARTS:
        qs = m["questions"][part]
        assert len(qs) == 6
        assert sum(q["type"] == "factual" for q in qs) == 3
        for q in qs:
            assert q["answer"] in q["options"] and len(q["options"]) == 4
    # correct answers are spread over A-D (no answer-position giveaway)
    answers = pd.Series([q["answer"] for p in logic.PARTS for q in m["questions"][p]])
    assert answers.value_counts().max() <= 4


def test_score_part():
    qs = logic.load_materials()["questions"]["A"]
    perfect = {q["id"]: q["answer"] for q in qs}
    assert logic.score_part(perfect, qs) == 6
    assert logic.score_part({}, qs) == 0


def test_ingest_produces_pipeline_files(tmp_path):
    m = logic.load_materials()
    rows = []
    for i in range(4):
        r = logic.empty_record()
        seq = 1 + i % 2
        r.update(participant_id=f"P-{i}", is_pilot=str(i == 3), sequence=seq,
                 p1_method=logic.SEQUENCES[seq]["A"], p2_method=logic.SEQUENCES[seq]["B"])
        for p, part in (("p1", "A"), ("p2", "B")):
            for j, q in enumerate(m["questions"][part], start=1):
                r[f"{p}_q{j:02d}"] = q["answer"]
        rows.append(r)
    app_file = tmp_path / "app_responses.csv"
    pd.DataFrame(rows, columns=logic.FIELDNAMES).to_csv(app_file, index=False)

    ingest_app_data.main(["--app-file", str(app_file), "--out-dir", str(tmp_path / "raw"),
                          "--pilot-dir", str(tmp_path / "pilot")])
    quiz = pd.read_csv(tmp_path / "raw" / "quiz_responses.csv")
    assign = pd.read_csv(tmp_path / "raw" / "assignments.csv")
    assert len(quiz) == 6 and len(assign) == 6          # 3 real participants x 2 parts
    assert (tmp_path / "pilot" / "app_responses_pilot.csv").exists()
    assert set(assign["method"]) == {"handwritten", "ai"}
    assert (tmp_path / "raw" / "answer_key.csv").exists()


class FakeWorksheet:
    def __init__(self, values):
        self.values = values

    def row_values(self, i):
        return [c for c in self.values[i - 1] if c] if len(self.values) >= i else []

    def get_all_values(self):
        return self.values

    def append_row(self, row, value_input_option=None):
        self.values = [v for v in self.values if any(v)] + [list(row)]


def test_header_written_to_empty_sheet_in_any_gspread_format():
    import pytest
    import storage

    for empty in ([], [[]], [[""]]):
        ws = FakeWorksheet(empty)
        storage.ensure_header(ws)
        assert ws.values[0] == logic.FIELDNAMES
        storage.ensure_header(ws)  # second call is a no-op
        assert len(ws.values) == 1

    with pytest.raises(RuntimeError):
        storage.ensure_header(FakeWorksheet([["something else"]]))
