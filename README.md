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
- **Allocation:** Efron's biased coin. Every start is logged (Google Sheet `allocations` tab) before Part 1; the sequence with fewer started (non-pilot) participants is assigned with probability 2/3 (1/2 when tied). This keeps the sample close to balanced while staying random even when many people start at once, and lets us report drop-out by sequence.

## Research question and hypotheses

| | |
|---|---|
| **H0** | Mean immediate quiz score is the same for handwritten and AI-summary study (mean paired difference = 0). |
| **H1** | The means differ. |
| **Test** | Two-tailed paired t-test on each participant's score difference, alpha = 0.05. Two-tailed because AI summaries could help *or* hurt. |
| **Primary outcome** | Quiz score (% correct) for each part, compared by method. |
| **Secondary (exploratory)** | Factual vs. conceptual subscores; robustness on items fully covered by the AI summary (`summary_coverage`); self-predicted score vs. actual; sequence × method (carryover); review time, device and note-taking/AI habits as covariates or moderators. |
| **Sample size** | Target 24-30 participants. Planned power calculation: 80% power to detect d_z = 0.6 needs 24 complete pairs. |
| **Exclusions** | Prior knowledge of tardigrades >= 4 (of 5); failed attention check; did not follow a method (no handwritten notes, did not read the summary, or wrote notes in the AI part); looked at notes/summary during a quiz. Paused/rewound is reported and checked in a sensitivity analysis. People who did the study before or had already seen the video are stopped by the app; pilot rows are excluded automatically. |

## Known limitations (to discuss in the report)

- We compare two complete study **strategies** (own handwritten notes vs. reading an AI summary), so we cannot separate the effect of writing from the effect of who wrote the notes.
- Part 1 (137 s) is longer than Part 2 (98 s) and always comes first; method order is counterbalanced, but carryover may differ by order (e.g., knowing the quiz format helps second-half note-takers more), so the analysis includes a sequence × method check.
- The AI summary covers 6 of 12 quiz answers fully, 4 partially and 2 not at all (`summary_coverage`); a robustness analysis uses only fully covered items.
- "Conceptual" items still ask about content stated in the video; the factual/conceptual split is exploratory.
- Six items per part give coarse scores; item-level models use all 12 answers per person.
- Online, unsupervised sessions: compliance, pausing/rewinding and use of materials are self-reported.

## Project status

| Item | Status |
|---|---|
| Experimental design | Done (above) |
| Streamlit data-collection app | Done and deployed (link above) |
| Quiz questions and video segments | In [`materials/study_materials.json`](materials/study_materials.json) |
| ChatGPT summaries | Generated once with GPT-6 (ChatGPT) and pasted in; prompt and outputs in `materials/ai_prompt.md` |
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

Locally, responses are saved to `data/app_responses/responses.csv` and starts to `data/app_responses/allocations.csv`
(both git-ignored). The deployed app saves to a Google Sheet (first tab: completed participants; `allocations` tab: starts); see [`docs/app_setup.md`](docs/app_setup.md) for the secrets setup, deployment, and what
each saved field means.

## Getting the data out

1. In the Google Sheet, download the first tab as CSV to `data/raw/app_responses.csv` and the `allocations`
   tab to `data/raw/app_allocations.csv` (File -> Download -> CSV). Do not edit them.
2. Convert them into the analysis tables:

```bash
python src/ingest_app_data.py     # -> data/raw/: quiz_responses, assignments, answer_key, participants,
                                  #    session_process, allocations (drop-out)
```

## Data and privacy

Participants appear only as random IDs (`P-XXXXXXXX`); no names or emails are collected.
Pilot rows are written separately to `data/pilot/` and never analyzed.

## Contributing

Work happens on branches and pull requests; see [`CONTRIBUTING.md`](CONTRIBUTING.md).
