# Analysis plan

This document describes the analysis implemented by the scripts in `src/`.

## Question and hypotheses

Do people remember more from a short educational video when they take their own handwritten
notes than when they only watch and then read a ChatGPT summary?

- **H0:** the mean quiz score is the same under both methods (mean paired difference = 0).
- **H1:** the mean quiz scores differ (two-tailed: the AI summary could help or hurt).

## Variables

| | |
|---|---|
| Independent variable | Study method, within subjects: handwritten notes vs. AI summary |
| Dependent variable | Quiz score for that part, % correct out of 6 questions |
| Control | Same video, same review screen, same quiz format; method order counterbalanced (sequence 1 / 2) |
| Randomization | Sequence assigned by Efron's biased coin when the participant starts |

## Sample size

A priori power analysis (`src/power_analysis.py`): two-tailed paired t-test, alpha = 0.05,
power = 0.80, smallest effect of interest d_z = 0.6 → **24 complete participants**.
16 participants completed the study, which gives a power of 0.61 for the same effect.

## Data

All 16 participants who completed both parts are analysed. Pilot sessions are flagged by the app
and never analysed.

## Primary analysis (`src/paired_ttest.py`)

1. Score each part as % correct; compute each person's difference (handwritten minus AI).
2. Check the paired differences: Shapiro-Wilk test and outliers (|z| > 3).
3. **Two-tailed paired t-test**, alpha = 0.05: mean difference with its 95% CI, t, df, p and
   Cohen's d_z.
4. **Wilcoxon signed-rank test** (with rank-biserial r), as a check that does not assume normal
   differences.

## Secondary analyses (`src/secondary_analysis.py`)

- **Question type (post hoc):** the same paired comparison on factual questions, conceptual
  questions and questions fully covered by the AI summary, Holm-corrected.
- **Order check:** Welch t-test on the paired differences between sequence 1 and sequence 2.
- **Confidence:** predicted minus actual score, compared between methods.
