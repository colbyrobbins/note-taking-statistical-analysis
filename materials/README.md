# Study materials

Everything participants see, so the study can be reproduced exactly:

- `study_materials.json`: the video (TED-Ed, "Meet the tardigrade, the toughest animal on Earth",
  Thomas Boothby; https://www.youtube.com/watch?v=IxndOd3kmSs), the two segments (Part 1 "A":
  0:00–2:17, Part 2 "B": 2:17–3:55), the ChatGPT summary of each part, and the 12 quiz items
  (6 per part: 3 factual, 3 conceptual) with the keyed answer and `summary_coverage` for each.
  The app reads this file directly; `src/ingest_app_data.py` builds `answer_key.csv` from it.
- `ai_prompt.md`: how the AI summaries were made (exact prompt, model, date, source transcript),
  the outputs as generated, and the coverage check of each quiz item.

Consent text, instructions and all other participant-facing wording live in `app/streamlit_app.py`.
Do not change any of these files while data is being collected.
