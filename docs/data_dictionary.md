# Data dictionary

All raw files go in `data/raw/`. Column names are case-insensitive. Participants are
identified only by ID (`P001`, ...).

## Raw

### `assignments.csv` (from `assign_conditions.py`)
| column | description |
|---|---|
| participant_id | `P001`, `P002`, ... |
| sequence | 1-4, see `config.SEQUENCES` |
| session_order | 1 = first video watched, 2 = second |
| video | `A` or `B` |
| method | `handwritten` or `ai` |

### `quiz_responses.csv` (Google Forms / Sheets export)
One row per quiz submission, i.e. participant x video x timepoint.
| column | description |
|---|---|
| timestamp | optional; if present, the earliest duplicate submission is kept |
| participant_id | must match `assignments.csv` |
| video | `A` or `B` |
| timepoint | `immediate` or `delayed` (48 hours) |
| q01 ... qNN | the answer chosen, e.g. `A`-`D`. Blank = unanswered (scored incorrect) |

Tip: add `participant_id`, `video`, and `timepoint` as required short-answer (or
pre-filled link) fields in each Form so the export needs no manual editing.

### `answer_key.csv`
| column | description |
|---|---|
| video | `A` or `B` |
| question_id | `q01`... matching the response columns |
| question_type | `factual` or `conceptual` |
| correct_answer | e.g. `C` |

## Processed (from `clean_data.py`)

### `scores_long.csv`
One row per participant x video x timepoint: `n_questions`, `n_correct`, `pct_total`,
`pct_factual`, `pct_conceptual`, plus `method` and `sequence`.

### `scores_wide.csv`
One row per participant with **all four** scores present:
`handwritten_immediate`, `handwritten_delayed`, `ai_immediate`, `ai_delayed`
(each % correct), plus `sequence` and `first_method`. This is the input to `analyze.py`.

## Results (`results/tables/`)
- `power_analysis.csv`: required n by effect size
- `exclusions.csv`: participants dropped and which scores were missing
- `primary_results.csv`: paired t-test for the delayed (primary) and immediate (secondary) quiz
- `assumption_checks.csv`: Shapiro-Wilk, Wilcoxon, order-effect check
