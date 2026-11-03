# Handwritten Notes vs. AI Summaries

Module Project 2 (Statistical Analysis), AIPI 510, Duke University. Alberto Gomez Soteres and Colby Robbins.

Do people remember more from a short video when they take their own handwritten notes than when
they read a ChatGPT summary? We ran a within-subjects experiment to find out.

**Live study app:** https://note-taking-statistical-analysis.streamlit.app/

## Result in one paragraph

16 participants completed the study. They scored **89.6%** with handwritten notes and **75.0%**
with the AI summary, a difference of **+14.6 points** (95% CI [0.5, 28.7], d_z = 0.55). The paired
t-test was significant (t(15) = 2.21, p = .043); the Wilcoxon signed-rank test was not
(p = .057), and Shapiro-Wilk showed the differences were not normal (p = .012). Most of the gap
came from conceptual questions (+25.0 points, p = .029, Holm p = .086). We read this as early
evidence in favor of handwritten notes, not a final answer.

## Experimental design

Every participant watched the same TED-Ed video, "Meet the tardigrade, the toughest animal on Earth",
split into Part 1 (0:00-2:17) and Part 2 (2:17-3:55). Each part used a different study method:

| Sequence | Part 1 | Part 2 |
|---|---|---|
| 1 | Handwritten notes | ChatGPT summary |
| 2 | ChatGPT summary | Handwritten notes |

- **Handwritten:** take notes on paper while watching, review them, put them away, take the quiz.
- **AI summary:** only watch, then read a fixed ChatGPT summary of that part, then take the quiz
  (prompt and outputs in [`materials/ai_prompt.md`](materials/ai_prompt.md)).
- **Quiz:** 6 multiple-choice questions per part (3 factual, 3 conceptual).
- **Counterbalancing:** each part is studied with both methods across the sample, so differences in
  difficulty between parts cancel out.
- **Randomization:** Efron's biased coin assigns each new participant to a sequence (8 ended up in each).

## Hypotheses and analysis

| | |
|---|---|
| **H0** | Mean quiz score is the same with handwritten notes and with the AI summary |
| **H1** | The means differ (two-tailed, alpha = 0.05) |
| **Power analysis** | 24 participants for 80% power to detect d_z = 0.6 (`src/power_analysis.py`); with the 16 collected, power is 0.61 |
| **Primary test** | Paired t-test on each person's handwritten minus AI score, with a Shapiro-Wilk check and the Wilcoxon signed-rank test |
| **Secondary** | Post hoc tests by question type (Holm-corrected), order check, predicted vs. actual score |

Full plan: [`docs/analysis_plan.md`](docs/analysis_plan.md).

## Repository layout

```
app/                    Streamlit study app (data collection)
  streamlit_app.py        participant-facing pages
  logic.py                sequences, allocation, scoring; no Streamlit imports
  storage.py              saves responses to a Google Sheet (local CSV when run locally)
src/                    analysis scripts, in the order they run
  power_analysis.py       a priori power analysis and power tables
  ingest_app_data.py      Google Sheet export -> raw analysis tables in data/raw/
  clean_data.py           scoring -> clean tables in data/processed/
  paired_ttest.py         primary analysis: paired t-test, Shapiro-Wilk, Wilcoxon
  secondary_analysis.py   descriptives, post hoc tests, order check, confidence
  make_figures.py         the five figures used in the report
  run_pipeline.py         runs every step above in order
tests/                  pytest checks for the app logic and every analysis step
data/raw/               app export (app_responses.csv) and the tables derived from it
data/processed/         scored, clean data (one row per question, per part and per participant)
results/                tables and figures written by the scripts
docs/                   analysis plan and app setup guide (with a field-by-field data dictionary)
materials/              video details, quiz questions and answer key, ChatGPT prompt and summaries
```

## Reproducing the analysis

Requires Python 3.10+.

```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
python src/run_pipeline.py      # every number and figure in the report
pytest                          # 24 tests
```

Or step by step:

```bash
python src/power_analysis.py                       # -> results/power_*.csv
python src/ingest_app_data.py                      # -> data/raw/ analysis tables
python src/clean_data.py                           # -> data/processed/
python src/paired_ttest.py                         # -> results/paired_ttest.csv
python src/secondary_analysis.py                   # -> results/descriptives.csv, secondary_tests.csv
python src/make_figures.py                         # -> results/figures/
```

## Data

- `data/raw/app_responses.csv`: one row per participant who completed the study (16), exported
  from the Google Sheet with the columns used in the analysis: sequence, background answers,
  method, quiz answers and predicted score for each part.
- `data/raw/*.csv` (other files): the same data reshaped by `src/ingest_app_data.py`, plus the answer key.
- `data/processed/`: scored data built by `src/clean_data.py`; never edited by hand.

Participants appear only as random IDs (`P-XXXXXXXX`); no names, emails or IP addresses were collected.

## Running the app

```bash
streamlit run app/streamlit_app.py     # http://localhost:8501 (add ?pilot=1 for pilot mode)
```

Locally, responses are saved to `data/app_responses/` (git-ignored). The deployed app saves to a
Google Sheet; see [`docs/app_setup.md`](docs/app_setup.md) for the setup and what each saved field means.

## Contributing

Work happens on branches and pull requests into `dev`; see [`CONTRIBUTING.md`](CONTRIBUTING.md).
