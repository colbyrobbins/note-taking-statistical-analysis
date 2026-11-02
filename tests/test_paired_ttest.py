import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import paired_ttest as pt  # noqa: E402

SECONDS = {"A": 137, "B": 98}
KEY = pd.DataFrame([{"video": v, "question_id": f"q{i:02d}", "correct_answer": "A"}
                    for v in "AB" for i in range(1, 7)])


def quiz_row(pid, video, n_correct):
    answers = {f"q{i:02d}": "A" if i <= n_correct else "B" for i in range(1, 7)}
    return {"participant_id": pid, "video": video, "timepoint": "immediate", **answers}


def assign_rows(pid, sequence):
    methods = ("handwritten", "ai") if sequence == 1 else ("ai", "handwritten")
    return [{"participant_id": pid, "sequence": str(sequence), "session_order": str(i + 1),
             "video": v, "method": m} for i, (v, m) in enumerate(zip("AB", methods))]


def test_known_answer():
    hand = np.array([80, 70, 90, 60, 75.0])
    ai = np.array([70, 65, 80, 55, 70.0])
    res = pt.paired_tests(hand, ai)
    d = hand - ai
    t = d.mean() / (d.std(ddof=1) / np.sqrt(len(d)))
    assert res["t"] == pytest.approx(t)
    assert res["p_t"] == pytest.approx(2 * stats.t.sf(abs(t), len(d) - 1))
    assert res["cohens_dz"] == pytest.approx(d.mean() / d.std(ddof=1))
    assert res["df"] == 4
    half = stats.t.ppf(0.975, 4) * d.std(ddof=1) / np.sqrt(5)
    assert res["ci95_low"] == pytest.approx(d.mean() - half)
    assert res["ci95_high"] == pytest.approx(d.mean() + half)


def test_sign_is_handwritten_minus_ai():
    res = pt.paired_tests([90, 80, 85, 70], [60, 70, 65, 50])
    assert res["mean_diff"] > 0 and res["t"] > 0 and res["rank_biserial_r"] > 0
    assert pt.paired_tests([60, 70, 65, 50], [90, 80, 85, 70])["mean_diff"] < 0


def test_scoring_is_percent_correct():
    quiz = pd.DataFrame([quiz_row("P1", "A", 6), quiz_row("P1", "B", 3)])
    scores = pt.score_parts(quiz, KEY).set_index(["participant_id", "video"])["pct"]
    assert scores[("P1", "A")] == pytest.approx(100)
    assert scores[("P1", "B")] == pytest.approx(50)


def test_methods_map_to_the_right_part_in_both_sequences():
    quiz = pd.DataFrame([quiz_row("P1", "A", 6), quiz_row("P1", "B", 3),
                         quiz_row("P2", "A", 6), quiz_row("P2", "B", 3)])
    assignments = pd.DataFrame(assign_rows("P1", 1) + assign_rows("P2", 2))
    wide = pt.method_scores(pt.score_parts(quiz, KEY), assignments)
    assert (wide.loc["P1", "handwritten"], wide.loc["P1", "ai"]) == (100, 50)  # Part 1 handwritten
    assert (wide.loc["P2", "handwritten"], wide.loc["P2", "ai"]) == (50, 100)  # Part 2 handwritten
    assert wide.loc["P1", "diff"] == 50 and wide.loc["P2", "diff"] == -50


def process_rows(pid, **override):
    base = {"watch_seconds": "200", "compliance": "Yes", "used_material_during_quiz": "No"}
    rows = []
    for v, method in zip("AB", ("handwritten", "ai")):
        row = {"participant_id": pid, "video": v, **base,
               "ai_part_wrote_notes": "No" if method == "ai" else "n/a"}
        row.update(override.get(v, {}))
        rows.append(row)
    return rows


@pytest.mark.parametrize("rule, background, process", [
    ("prior_knowledge_high", {"prior_knowledge": "4"}, {}),
    ("failed_attention_check", {"attention_check": "Never"}, {}),
    ("short_watch", {}, {"B": {"watch_seconds": "90"}}),
    ("did_not_follow_method", {}, {"A": {"compliance": "No"}}),
    ("ai_part_wrote_notes", {}, {"B": {"ai_part_wrote_notes": "Yes"}}),
    ("used_material_in_quiz", {}, {"A": {"used_material_during_quiz": "Yes"}}),
])
def test_each_exclusion_rule_drops_only_that_person(rule, background, process):
    ok = {"prior_knowledge": "2", "attention_check": "Often"}
    participants = pd.DataFrame([{"participant_id": "bad", **ok, **background},
                                 {"participant_id": "good", **ok}])
    proc = pd.DataFrame(process_rows("bad", **process) + process_rows("good"))
    flags = pt.exclusion_flags(participants, proc, SECONDS)
    assert flags.loc["bad", rule]
    assert flags.loc["bad"].sum() == 1
    assert not flags.loc["good"].any()


def test_too_few_pairs_gives_clear_error():
    with pytest.raises(ValueError, match="at least 2"):
        pt.paired_tests([80.0], [70.0])


def test_main_writes_results_from_synthetic_raw_tables(tmp_path):
    raw, out = tmp_path / "raw", tmp_path / "results"
    raw.mkdir()
    n_correct = [(5, 3), (6, 4), (4, 4), (5, 2), (6, 3), (3, 3)]  # (handwritten, ai)
    quiz, assign, parts, proc = [], [], [], []
    for i, (h, a) in enumerate(n_correct):
        pid, seq = f"P{i}", 1 + i % 2
        a_score, b_score = (h, a) if seq == 1 else (a, h)
        quiz += [quiz_row(pid, "A", a_score), quiz_row(pid, "B", b_score)]
        assign += assign_rows(pid, seq)
        parts.append({"participant_id": pid, "prior_knowledge": "1", "attention_check": "Often"})
        proc += process_rows(pid)
    pd.DataFrame(quiz).to_csv(raw / "quiz_responses.csv", index=False)
    pd.DataFrame(assign).to_csv(raw / "assignments.csv", index=False)
    pd.DataFrame(parts).to_csv(raw / "participants.csv", index=False)
    pd.DataFrame(proc).to_csv(raw / "session_process.csv", index=False)
    KEY.to_csv(raw / "answer_key.csv", index=False)

    pt.main(["--raw-dir", str(raw), "--results-dir", str(out)])
    row = pd.read_csv(out / "paired_ttest.csv").iloc[0]
    assert row["n_pairs"] == 6 and row["n_excluded"] == 0
    diffs = np.array([(h - a) / 6 * 100 for h, a in n_correct])
    assert row["mean_diff"] == pytest.approx(diffs.mean())


def test_no_exclusions_keeps_excluded_people_and_writes_a_separate_file(tmp_path):
    raw, out = tmp_path / "raw", tmp_path / "results"
    raw.mkdir()
    n_correct = [(5, 3), (6, 4), (4, 4), (5, 2)]
    quiz, assign, parts, proc = [], [], [], []
    for i, (h, a) in enumerate(n_correct):
        pid, seq = f"P{i}", 1 + i % 2
        a_score, b_score = (h, a) if seq == 1 else (a, h)
        quiz += [quiz_row(pid, "A", a_score), quiz_row(pid, "B", b_score)]
        assign += assign_rows(pid, seq)
        parts.append({"participant_id": pid, "prior_knowledge": "5" if i == 0 else "1", "attention_check": "Often"})
        proc += process_rows(pid)
    for name, rows in [("quiz_responses", quiz), ("assignments", assign),
                       ("participants", parts), ("session_process", proc)]:
        pd.DataFrame(rows).to_csv(raw / f"{name}.csv", index=False)
    KEY.to_csv(raw / "answer_key.csv", index=False)

    pt.main(["--raw-dir", str(raw), "--results-dir", str(out)])
    pt.main(["--raw-dir", str(raw), "--results-dir", str(out), "--no-exclusions"])
    primary = pd.read_csv(out / "paired_ttest.csv").iloc[0]
    everyone = pd.read_csv(out / "paired_ttest_no_exclusions.csv").iloc[0]
    assert (primary["n_pairs"], primary["n_excluded"]) == (3, 1)  # P0 has high prior knowledge
    assert (everyone["n_pairs"], everyone["n_excluded"]) == (4, 0)
