# Data-collection app: setup, pilot and export

The study runs as a Streamlit app (`app/streamlit_app.py`). Participants open one public link,
the app assigns them a counterbalanced sequence, and each completed session is saved as one row.

## 1. Run it locally (2 minutes)

```bash
pip install -r requirements.txt
streamlit run app/streamlit_app.py            # http://localhost:8501
# pilot mode (rows flagged is_pilot=True and excluded from the analysis):
#   http://localhost:8501/?pilot=1
```

Without secrets, responses are saved to `data/app_responses/responses.csv` (git-ignored).

## 2. Before launch: paste the ChatGPT summaries

1. Open a **new** ChatGPT chat. For each half, paste the prompt in `materials/ai_prompt.md`
   followed by the English transcript of that half (Part 1: 0:00–2:17, Part 2: 2:17–3:55).
2. Paste each output, unchanged, into `ai_summary` for part `A` and part `B` in
   `materials/study_materials.json`.
3. Record the model name and date in `materials/ai_prompt.md`.

Until both summaries are pasted, the public app shows "not open yet" (pilot mode still works).

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

The app writes the header row on first use. **Never commit the JSON key.**

## 4. Deploy (Streamlit Community Cloud, free)

share.streamlit.io → New app → repository `colbyrobbins/note-taking-statistical-analysis`,
branch `main` (or `dev` for the pilot), main file `app/streamlit_app.py` → paste the secrets → Deploy.

## 5. Pilot (2–3 people)

Send `<app-url>/?pilot=1`. Check: total time about 10 minutes, nobody scores 6/6 on both parts by
guessing, the video segments start and stop correctly, and rows appear in the sheet with
`is_pilot = True`.

## 6. Export and analyze

1. Google Sheet → File → Download → CSV → save as `data/raw/app_responses.csv`
   (this is the untouched raw data; do not edit it).
2. Run:

```bash
python src/ingest_app_data.py   # app export -> quiz_responses, assignments, answer_key, participants, session_process
```

The cleaning and analysis scripts then read these files from `data/raw/`.

## What the app records (one row per completed participant)

| Field | Meaning |
|---|---|
| `participant_id` | Random ID (`P-XXXXXXXX`); no personal data is collected |
| `is_pilot`, `app_version`, `started_at`, `completed_at` | Session metadata (UTC timestamps) |
| `sequence` | 1 = Part 1 handwritten / Part 2 AI; 2 = Part 1 AI / Part 2 handwritten |
| `student_status`, `native_english`, `usual_note_method`, `ai_summary_use` | Sample description |
| `prior_knowledge` (1–5) | Exclusion rule (≥ 4) |
| `attention_check` | Must equal `Often` |
| `p1_*` / `p2_*` `method` | Method used for that half |
| `p1_*` / `p2_*` `watch_seconds`, `review_seconds`, `review_timed_out`, `quiz_seconds` | Timing; review is self-paced with a 120 s cap |
| `p1_q01`…`p1_q06`, `p2_q01`…`p2_q06` | Chosen option (A–D); scored later against `answer_key.csv` |
| `p1_*` / `p2_*` `predicted_correct` (0–6) | Self-predicted score (confidence gap) |
| `p1_*` / `p2_*` `compliance` | Followed the method instructions (Yes / Partly / No) |
| `p1_*` / `p2_*` `used_material_during_quiz` | Self-reported looking at notes/summary during the quiz |

Allocation: each new participant gets whichever sequence has fewer completed, non-pilot
participants (random tie-break), so the two sequences stay balanced in the final sample.
