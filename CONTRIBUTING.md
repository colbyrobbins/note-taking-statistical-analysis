# Contributing

The course requires branches and pull requests, with at least one PR from each team member.

## Workflow

1. Branch from an up-to-date `main`: `git switch main && git pull && git switch -c feature/<short-name>`
   (e.g. `feature/power-analysis`, `feature/clean-data`, `docs/report-outline`).
2. Make small, focused commits with clear messages.
3. Run `pytest` before pushing.
4. Open a pull request into `main` using the PR template (`docs/pull_request_template.md`; move it to `.github/` so GitHub pre-fills it). Link the issue if there is one.
5. The other teammate reviews: read the diff, run the code if it changes results,
   and leave specific comments. Resolve every comment before merging.
6. Squash-merge, then delete the branch.

Do not push directly to `main`.

## Conventions

- Code lives in `src/` as scripts, not notebooks. Constants belong in `src/config.py`.
- Never commit anything that identifies a participant. Use IDs only.
- Never edit files in `data/raw/` by hand after collection; fix problems in `clean_data.py`
  so the cleaning is reproducible.
- Generated outputs in `results/` should be reproducible from the scripts.
