# Contributing

The course requires branches and pull requests, with at least one PR from each team member.

## Workflow

1. Branch from an up-to-date `dev`: `git switch dev && git pull && git switch -c feature/<short-name>`
   (e.g. `feature/power-analysis`, `feature/clean-data`, `docs/report-outline`).
2. Make small, focused commits with clear messages.
3. Run `pytest` before pushing.
4. Open a pull request into **`dev`** (not `main`). Link the issue if there is one.
5. The other teammate reviews: read the diff, run the code if it changes results,
   and leave specific comments. Resolve every comment before merging.
6. Squash-merge, then delete the branch.

Do not push directly to `dev` or `main`. `main` only receives the final, reviewed merge from `dev`.

**During data collection, do not merge changes to `app/` or `materials/`**: the deployed app redeploys
from `dev` automatically. If a fix is unavoidable, bump `APP_VERSION` in `app/logic.py` so affected rows
can be identified.

## Conventions

- Code lives in `app/` (data collection) and `src/` (analysis) as scripts, not notebooks.
- Never commit anything that identifies a participant. Use IDs only.
- Never edit files in `data/raw/` by hand after collection; fix problems in the cleaning script
  so the cleaning is reproducible.
- Generated outputs in `results/` should be reproducible from the scripts.
