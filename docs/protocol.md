# Experimental protocol

Items marked **OPEN** are assumptions I carried over from the project idea or
filled in to make the scaffold runnable. Confirm or change them before data
collection, and update `src/config.py` to match.

## Design

- **Within-subject (crossover)**: every participant studies both methods.
- **Independent variable**: note method, with two levels: `handwritten`, `ai`.
- **Dependent variable**: quiz score (% correct) at two times: immediately after
  each video and 48 hours later. Primary outcome is the 48-hour score.
- **Materials**: two ~6-minute educational videos (A and B).
  **OPEN**: choose videos of similar difficulty, on topics participants are unlikely to know.
- **Counterbalancing**: four sequences cross video order with method order
  (`config.SEQUENCES`). Participants are assigned in shuffled blocks of four
  (`assign_conditions.py`), so video difficulty and practice effects do not line
  up with one method.

## Procedure (about 30 minutes, plus a short follow-up)

1. Consent; participant is given an ID.
2. Video 1 with the first assigned method; immediate quiz.
3. Video 2 with the other method; immediate quiz.
4. 48 hours later: delayed quiz for both videos (link sent by email/text).

Method definitions:

- **Handwritten**: participant takes notes with pen and paper while watching.
- **AI**: participant receives a ChatGPT-generated summary of the video and studies it.
  **OPEN**: is the summary generated once from the transcript with a fixed prompt
  (recommended, so every participant sees the same text), or does each participant
  prompt ChatGPT live? Record the exact prompt and model version in `materials/`.
- **OPEN**: time allowed to review notes before the quiz, if any (keep equal across methods).

## Quiz

- 10 multiple-choice items per video: 5 factual, 5 conceptual (**OPEN**: item counts).
- The same items are used immediately and at 48 hours (**OPEN**: this allows a
  retest effect; the effect is shared by both methods, so it should not bias the
  paired comparison, but note it as a limitation).
- Multiple choice lets `clean_data.py` score automatically against `answer_key.csv`.

## Hypotheses

- H0: mu_AI = mu_hand (mean paired difference in 48-hour score is 0).
- H1: mu_AI != mu_hand. The expected direction is that AI helps, but the test is
  two-tailed because it could be worse.
- alpha = 0.05, two-tailed.

## Power analysis

Paired t-test, d_z = 0.6, alpha = 0.05 two-tailed, power = 0.80 gives **24 complete
pairs** (`src/power_analysis.py`, exact noncentral-t calculation). With an assumed
15% loss at the 48-hour follow-up, recruit **29**. d_z = 0.6 is an assumption taken
from the project idea; the sensitivity table in `results/tables/power_analysis.csv`
shows n for d_z from 0.4 to 0.8 (0.4 needs 52 pairs).

## Analysis plan

1. Clean and score (`clean_data.py`). Participants missing any of the four scores
   (method x timepoint) are excluded and logged in `results/tables/exclusions.csv`.
2. Primary: two-tailed paired t-test on 48-hour scores (AI minus handwritten);
   report t, df, p, 95% CI of the mean difference, Cohen's d_z and Hedges' g_z.
3. Assumption checks: Shapiro-Wilk on the paired differences, Wilcoxon signed-rank
   as a non-parametric backup, and an order check (Welch t-test of the differences
   between "AI first" and "handwritten first" participants).
4. Secondary/exploratory (no multiplicity correction, labeled as such): immediate
   score; factual vs. conceptual subscores (available in `scores_long.csv`).
5. If time allows: condition x timing analysis (does AI help immediately but hurt
   at 48 hours?). This is outside the single confirmatory test.

## Known risks

- Dropout at 48 hours (mitigated by recruiting extra; log everything).
- Video difficulty differences (mitigated by counterbalancing).
- Small sample and a convenience sample of students limit generalization.
