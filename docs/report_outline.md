# Written report outline

Mapped to the Project Guidelines. The right column says where each piece comes from.

| Section | Source in this repo |
|---|---|
| Title & Abstract | write last |
| Background & Motivation | pen-vs-laptop literature (2014 original, 2021 replication) plus the AI-notes gap; add references |
| Null and Alternative Hypotheses | `docs/protocol.md` |
| Experimental Design (IV/DV, control, randomization) | `docs/protocol.md`, `src/config.py`, `src/assign_conditions.py` |
| Power Analysis (assumptions + calculations) | `src/power_analysis.py`, `results/tables/power_analysis.csv`, `results/figures/power_curve.png` |
| Data Collection & Cleaning | `docs/data_dictionary.md`, `src/clean_data.py`, `results/tables/exclusions.csv` |
| Statistical Analysis (test, rationale, assumptions, p, CI, effect size, post hoc) | `src/analyze.py`, `results/tables/primary_results.csv`, `assumption_checks.csv` |
| Interpretation of Results | figures from `src/plots.py` |
| Limitations | dropout, retest effect, convenience sample, AI-summary definition, small n |
| Conclusion and Recommendations | |
| References | |

Presentation (8 minutes, Nov 3): motivation, question and hypothesis, design,
key result and figures, takeaways and limitations.
