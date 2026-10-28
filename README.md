# Pen vs. ChatGPT: Does the Way You Take Notes Change What You Remember?

Module Project 2 (Statistical Analysis). A within-subject experiment comparing
**handwritten notes** with an **AI-generated (ChatGPT) summary**, scored on a short
multiple-choice quiz taken immediately after each half of a video.

**Live study app:** https://note-taking-statistical-analysis.streamlit.app/

## Experimental design

Every participant watches the same ~4-minute video, "Meet the tardigrade, the toughest animal on Earth"
(TED-Ed), split into two parts: Part 1 (0:00-2:17) and Part 2 (2:17-3:55). Each part uses a different
study method, and the order of methods is counterbalanced across two sequences:

| Sequence | Part 1 | Part 2 |
|---|---|---|
| 1 | Handwritten notes | ChatGPT summary |
| 2 | ChatGPT summary | Handwritten notes |

- **Handwritten:** the participant takes notes on paper while watching, reviews them (self-paced, max 2 minutes), then puts them away and takes the quiz.
- **AI summary:** the participant only watches, then reads a standardized ChatGPT summary of that part (same cap, same screen), which disappears when the quiz starts. The summaries were generated once and are shown unchanged to everyone (see [`materials/ai_prompt.md`](materials/ai_prompt.md)).
- **Quiz:** 6 multiple-choice questions per part (3 factual, 3 conceptual), taken right after that part.
- **Why this design:** every participant tries both methods, so each person serves as their own control. Because each half is used with both methods, any difference in difficulty between the halves cancels out across sequences.
- **Allocation:** the app assigns each new participant to whichever sequence has fewer completed (non-pilot) participants, with random tie-breaking.

## Research question and hypotheses

| | |
|---|---|
| **H0** | Mean immediate quiz score is the same for handwritten and AI-summary study (mean paired difference = 0). |
| **H1** | The means differ. |
| **Test** | Two-tailed paired t-test on each participant's score difference, alpha = 0.05. Two-tailed because AI summaries could help *or* hurt. |
| **Primary outcome** | Quiz score (% correct) for each part, compared by method. |
| **Secondary (exploratory)** | Factual vs. conceptual subscores; whether the AI summary contained the answer (`summary_coverage`); self-predicted score vs. actual. |
| **Sample size** | Target 24-30 participants. Planned power calculation: 80% power to detect d_z = 0.6 needs 24 complete pairs. |
| **Exclusions** | Prior knowledge of tardigrades >= 4 (of 5), or failing the attention check. Pilot rows are excluded automatically. |

## Project status

| Item | Status |
|---|---|
| Experimental design | Done (above) |
| Streamlit data-collection app | Done and deployed (link above) |
| Quiz questions and video segments | In [`materials/study_materials.json`](materials/study_materials.json) |
| ChatGPT summaries | Generated and pasted in; model name still to be recorded in `materials/ai_prompt.md` |
| Pilot (2-3 people) | To do |
| Data collection | To do |
| Cleaning, power analysis, statistical analysis, figures | To do (scripts will go in `src/`) |
| Written report and presentation (Nov 3) | To do |

## Repository layout

```
app/                 Streamlit study app
  streamlit_app.py     participant-facing pages
  logic.py             study logic (sequences, allocation, scoring); no Streamlit imports
  storage.py           saves responses: Google Sheet when deployed, local CSV otherwise
src/
  ingest_app_data.py   app export -> raw analysis tables in data/raw/
tests/               pytest checks for the app logic and ingestion
data/raw/            untouched app export and tables derived from it
data/processed/      cleaned, scored data
results/             tables and figures written by scripts
docs/app_setup.md    app setup, deployment, pilot and export guide (and a field-by-field data dictionary)
materials/           video details, quiz items, and the ChatGPT prompt and summaries
```

## Running the app

Requires Python 3.10+.

```powershell
# Windows PowerShell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
```bash
# macOS / Linux
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

```bash
streamlit run app/streamlit_app.py     # http://localhost:8501
# add ?pilot=1 to the URL for pilot mode (rows are flagged and excluded from analysis)
pytest
```

Locally, responses are saved to `data/app_responses/responses.csv` (git-ignored). The deployed app saves
to a Google Sheet; see [`docs/app_setup.md`](docs/app_setup.md) for the secrets setup, deployment, and what
each saved field means.

## Getting the data out

1. In the Google Sheet: File -> Download -> CSV, saved as `data/raw/app_responses.csv`. Do not edit it.
2. Convert it into the analysis tables:

```bash
python src/ingest_app_data.py     # -> data/raw/: quiz_responses, assignments, answer_key, participants, session_process
```

## Data and privacy

Participants appear only as random IDs (`P-XXXXXXXX`); no names or emails are collected.
Pilot rows are written separately to `data/pilot/` and never analyzed.

## Contributing

Work happens on branches and pull requests; see [`CONTRIBUTING.md`](CONTRIBUTING.md).
