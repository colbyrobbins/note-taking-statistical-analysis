# Data-collection app: setup, pilot and export

The study runs as a Streamlit app (`app/streamlit_app.py`). Participants open one public link,
the app assigns them a counterbalanced sequence (logged as soon as they press "Begin"), and each
completed session is saved as one row.

## 1. Run it locally (2 minutes)

```bash
pip install -r requirements.txt
streamlit run app/streamlit_app.py            # http://localhost:8501
# pilot mode (rows flagged is_pilot=True and excluded from the analysis):
#   http://localhost:8501/?pilot=1
```

Without secrets, responses are saved to `data/app_responses/responses.csv` and starts to
`data/app_responses/allocations.csv` (both git-ignored).

## 2. ChatGPT summaries (done)

The two summaries were generated once (GPT-6 in ChatGPT, 2026-10-27), each in a new chat, from the
transcript of that half (Part 1: 0:00–2:17, Part 2: 2:17–3:55), and pasted unchanged into
`ai_summary` for parts `A` and `B` in `materials/study_materials.json`. The exact prompt, source
transcript, outputs and the per-question coverage check are in `materials/ai_prompt.md`.
If a summary is ever missing, the public app shows "not open yet" (pilot mode still works).

## 3. Google Sheet storage (needed for the deployed app)

Streamlit Community Cloud wipes its disk on every restart, so deployed responses go to a Google Sheet.

1. Create an empty Google Sheet (e.g. "note-taking-study-responses"). Copy its key from the URL:
   `docs.google.com/spreadsheets/d/<SHEET_KEY>/edit`.
2. In Google Cloud Console: create a project → enable **Google Sheets API** and **Google Drive API**
   → IAM & Admin → Service accounts → create one → Keys → Add key → JSON. Download the file.
3. Share the Google Sheet with the service account's email (it ends in `iam.gserviceaccount.com`)
   as **Editor**.
4. Add these secrets (locally in `.streamlit/secrets.toml`, which is git-ignored; on Streamlit
   Cloud under App settings → Secrets):

```toml
sheet_key = "<SHEET_KEY>"

[gcp_service_account]
type = "service_account"
project_id = "..."
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "...@....iam.gserviceaccount.com"
client_id = "..."
token_uri = "https://oauth2.googleapis.com/token"
```

The app writes the header rows on first use (and creates the `allocations` tab). If the app's fields
ever change, empty the first tab before the next session, otherwise the header check stops the app.
**Never commit the JSON key.** New Google Cloud organizations may block key creation
(`iam.disableServiceAccountKeyCreation`); an organization admin can override that policy for the project.

## 4. Deploy (Streamlit Community Cloud, free)

share.streamlit.io → New app → repository `colbyrobbins/note-taking-statistical-analysis`,
branch `dev`, main file `app/streamlit_app.py` → paste the secrets → Deploy. Only the repo owner can
deploy (Streamlit requires admin rights). The app redeploys automatically after every merge into
`dev`, so do not merge changes to `app/` or `materials/` while collecting data.

## 5. Pilot (2–3 people)

Send `<app-url>/?pilot=1`. Check: total time about 10 minutes, the video segments start and stop
correctly, scores are not at the ceiling, and rows appear in both tabs with `is_pilot = True`.
Also ask one person to answer the 12 questions **without** watching: if they get 4 or more of 6
in a part, the items are too guessable.

## 6. Export and analyze

1. Google Sheet → first tab → File → Download → CSV → save as `data/raw/app_responses.csv`
   (this is the untouched raw data; do not edit it).
   Then the **`allocations`** tab → Download → CSV → save as `data/raw/app_allocations.csv`
   (every participant who pressed "Begin": used for allocation and to report drop-out).
2. Run:

```bash
python src/ingest_app_data.py   # app export -> quiz_responses, assignments, answer_key, participants, session_process
```

The cleaning and analysis scripts then read these files from `data/raw/`.

## What the app records

**`allocations` tab** (created automatically): one row per participant who pressed "Begin",
written *before* Part 1: `participant_id`, `is_pilot`, `app_version`, `sequence`, `started_at`.

**First tab**: one row per completed participant:

| Field | Meaning |
|---|---|
| `participant_id` | Random ID (`P-XXXXXXXX`); no personal data is collected |
| `is_pilot`, `app_version`, `started_at`, `completed_at` | Session metadata (UTC timestamps) |
| `sequence` | 1 = Part 1 handwritten / Part 2 AI; 2 = Part 1 AI / Part 2 handwritten |
| `taken_before_or_seen_video` | Always "No" in saved rows: "Yes" (did the study before, even partly, or had seen the video) ends the session and nothing is saved |
| `age_range`, `student_status`, `native_english` | Sample description |
| `device` | Laptop/desktop, tablet or phone; covariate (watching on a phone may lower scores) |
| `usual_note_method`, `ai_summary_use` | Note-taking and AI habits; exploratory moderators |
| `prior_knowledge` (1–5) | Exclusion rule (≥ 4) |
| `attention_check` | Must equal `Often` |
| `p1_*` / `p2_*` `method` | Method used for that half |
| `p1_*` / `p2_*` `watch_seconds`, `review_seconds`, `review_timed_out`, `quiz_seconds` | Timing; review is self-paced with no time limit |
| `p1_q01`…`p1_q06`, `p2_q01`…`p2_q06` | Chosen option (A–D); scored later against `answer_key.csv` |
| `p1_*` / `p2_*` `predicted_correct` (0–6) | Self-predicted score (confidence gap) |
| `p1_*` / `p2_*` `compliance` | Followed the method (Yes / No): "No" if they ticked "did not take handwritten notes" or "did not read the AI summary" |
| `p1_*` / `p2_*` `ai_part_wrote_notes` | AI part only: ticked "wrote notes" (Yes / No); `n/a` in the handwritten part |
| `p1_*` / `p2_*` `paused_or_rewound` | Ticked "paused, rewound, skipped ahead or changed the speed" (Yes / No) |
| `p1_*` / `p2_*` `used_material_during_quiz` | Ticked "looked at notes, the summary or anything else while answering" (Yes / No) |

The four compliance fields come from one "honesty check" per part: a list of checkboxes with
"None of these" (which cannot be combined with other boxes); at least one box must be ticked.

Allocation: Efron's biased coin (Efron, 1971), counted over logged starts. If one sequence has
fewer started, non-pilot participants, it is assigned with probability 2/3; if tied, 1/2. The final sample stays close to
balanced, and participants who start at the same moment are still randomized (a purely
deterministic "fewest first" rule would send everyone starting together to the same sequence).
