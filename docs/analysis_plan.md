# Analysis plan

This plan was written before data collection and updated once, after the final app changes
(no time limit on review, Continue button always visible), to add the watch-time exclusion and
the review-time comparison. No results had been looked at when either version was written.
The scripts in `src/` implement this plan; anything not listed here is reported as exploratory.

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
| Control | Same video, same self-paced review screen (no time limit, review time recorded), same quiz format; method order counterbalanced (sequence 1 / 2) |
| Randomization | Sequence assigned by Efron's biased coin when the participant starts |

## Sample size

A priori power analysis (`src/power_analysis.py`): two-tailed paired t-test, alpha = 0.05,
power = 0.80, smallest effect of interest d_z = 0.6 → **24 complete participants**.
We aim for about 30 to allow for roughly 20% exclusions. Data collection stops when we reach
the target or when we need to start the final analysis before the presentation, whichever
comes first. We do not look at the results before collection stops.

## Exclusions

Applied in `src/clean_data.py`. A person is excluded entirely if, in either part, they:

1. rated their prior knowledge of tardigrades 4 or 5 out of 5,
2. failed the attention check,
3. left the video page before that part could have finished (watch time shorter than the part),
4. did not take handwritten notes, or did not read the AI summary,
5. wrote notes during the AI part,
6. looked at notes or other material while answering a quiz.

People who did the study before or had already seen the video are stopped by the app.
Pilot sessions are flagged and never analyzed.

## Primary analysis

1. Score each part as % correct; compute each person's difference (handwritten minus AI).
2. Check assumptions on the differences: Shapiro-Wilk test, histogram, outliers (|z| > 3).
3. **Two-tailed paired t-test**, alpha = 0.05. Report the mean difference with its 95% CI,
   t, df, p and Cohen's d_z (plus d_av for comparison with between-groups studies).
4. If the differences are clearly not normal (Shapiro-Wilk p < .05), the **Wilcoxon signed-rank
   test** (with rank-biserial r) is used for the decision. It is reported in every case.

## Secondary and exploratory analyses

- **Question type:** the same paired comparison on factual items, conceptual items and items
  fully covered by the AI summary. These three tests are Holm-corrected.
- **Order check:** Welch t-test on the paired differences between sequence 1 and sequence 2,
  to see whether part difficulty or carryover changes the method effect.
- **Sensitivity:** repeat the primary test with no exclusions, and without people who paused
  or rewound the video (allowed, but it gives extra time).
- **Review time:** compared between methods, since review is self-paced.
- **Confidence:** predicted minus actual score, compared between methods.
- **Drop-out:** starts vs. completions by sequence, from the allocations log.
