# Pen vs. ChatGPT: Does the Way You Take Notes Change What You Remember?

Module Project 2 (Statistical Analysis). A within-subject experiment comparing
**handwritten notes** with **AI-generated (ChatGPT) notes**, scored on a quiz
**48 hours** after watching a short educational video. It extends the well-known
pen-vs-laptop note-taking studies with an AI condition.

## Research question and hypotheses

| | |
|---|---|
| **H0** | Mean 48-hour quiz score is the same for handwritten and AI notes (mu_AI = mu_hand, i.e. mean paired difference = 0). |
| **H1** | The means differ (mu_AI != mu_hand). |
| **Test** | Two-tailed paired t-test, alpha = 0.05. Two-tailed because AI notes could help *or* hurt. |
| **Primary outcome** | 48-hour delayed quiz score (% correct). |
| **Secondary (exploratory)** | Immediate quiz score; factual vs. conceptual subscores. |
| **Power** | 80% to detect d_z = 0.6, which needs 24 complete pairs. Recruit ~29 for 15% dropout. |

Full design details are in [`docs/protocol.md`](docs/protocol.md).

## Repository layout

```
src/                 all analysis code (scripts, not notebooks)
  config.py            study constants: alpha, power, sequences, paths
  power_analysis.py    a-priori power / sample-size calculation
  assign_conditions.py counterbalanced participant schedule
  simulate_data.py     fake data in the raw format, for testing only
  clean_data.py        score Google Forms exports -> tidy CSVs
  analyze.py           paired t-test, CI, effect sizes, assumption checks
  plots.py             report figures
tests/               pytest checks that run the pipeline on simulated data
data/raw/            Google Forms exports, answer key, assignments (see docs/data_dictionary.md)
data/processed/      cleaned, scored CSVs
results/             tables and figures written by the scripts
docs/                protocol, data dictionary, report outline
materials/           video list and quiz items
```

## Reproducing the analysis

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

Then run the pipeline in order:

```bash
python src/power_analysis.py      # sample size -> results/tables/power_analysis.csv
python src/assign_conditions.py --n 30   # -> data/raw/assignments.csv
# ... run sessions, export Google Forms to data/raw/ (see docs/data_dictionary.md) ...
python src/clean_data.py          # -> data/processed/scores_*.csv, results/tables/exclusions.csv
python src/analyze.py             # -> results/tables/primary_results.csv, assumption_checks.csv
python src/plots.py               # -> results/figures/*.png
```

To check the pipeline before real data exists, use simulated data (never report it as a finding):

```bash
python src/simulate_data.py --out-dir data/simulated
python src/clean_data.py --raw-dir data/simulated --out-dir data/simulated/processed --results-dir data/simulated/results
python src/analyze.py --data-dir data/simulated/processed --results-dir data/simulated/results
pytest
```

## Data and privacy

Participants appear only as pseudonymous IDs (`P001`, ...). Any file linking IDs
to real names or emails must stay outside the repo (`data/private/` is git-ignored).

## Contributing

Work happens on branches and pull requests; see [`CONTRIBUTING.md`](CONTRIBUTING.md).
