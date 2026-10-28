"""Note-Taking & Learning Study: data-collection app (AIPI 510, Module Project 2).

Run locally:      streamlit run app/streamlit_app.py
Pilot mode:       add ?pilot=1 to the URL (rows are flagged and excluded from analysis)

Flow per participant (about 10 minutes):
    consent -> background -> setup
    -> Part 1: watch (method A) -> self-paced review (max 2 min, timed) -> quiz
    -> Part 2: watch (method B) -> self-paced review -> quiz
    -> save -> debrief and score
"""
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

sys.path.insert(0, str(Path(__file__).resolve().parent))
from logic import (  # noqa: E402
    APP_VERSION, ATTENTION_CORRECT, PARTS, REVIEW_MAX_SECONDS, SEQUENCES,
    choose_sequence, empty_record, load_materials, make_participant_id, score_part, summaries_missing,
)
from storage import get_store  # noqa: E402

st.set_page_config(page_title="Note-Taking & Learning Study", page_icon=":material/edit_note:", layout="centered")

NAVY = "#012169"
STEPS = ["consent", "background", "setup", "A_watch", "A_review", "A_quiz", "B_watch", "B_review", "B_quiz", "done"]
METHOD_LABEL = {"handwritten": "Handwritten notes", "ai": "AI summary"}

st.markdown(
    f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap');
:root {{
  --accent: {NAVY}; --accent-hover: #0b2f7e; --ink: #202124; --ink-2: #3c4043; --ink-3: #5f6368;
  --line: #dadce0; --line-soft: #e8eaed; --page: #f8f9fa; --surface: #ffffff; --tint: #eef2fa;
  --shadow-1: 0 1px 2px rgba(60,64,67,.30), 0 1px 3px 1px rgba(60,64,67,.15);
  --shadow-2: 0 1px 3px rgba(60,64,67,.30), 0 4px 8px 3px rgba(60,64,67,.15);
}}
html, body, .stApp, .stMarkdown, .stRadio, .stCheckbox, button, input, textarea {{
  font-family: 'Roboto', system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
}}
#MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"],
[data-testid="stHeaderActionElements"] {{ display: none !important; }}
header[data-testid="stHeader"] {{ background: transparent; height: 0; }}
.stApp {{ background: var(--page); }}
.block-container {{ max-width: 720px; padding-top: 2rem !important; padding-bottom: 4rem; }}

/* header card, Google Forms style */
.hero {{ background: var(--surface); border: 1px solid var(--line); border-top: 8px solid var(--accent);
         border-radius: 8px; padding: 22px 24px 20px; margin-bottom: 12px; }}
.hero .kicker {{ font-size: 12px; font-weight: 500; letter-spacing: .06em; color: var(--accent); text-transform: uppercase; }}
.hero h1 {{ font-size: 30px; line-height: 1.25; font-weight: 400; color: var(--ink); margin: 8px 0 6px; padding: 0; letter-spacing: 0; }}
.hero .names {{ color: var(--ink-2); font-size: 16px; font-weight: 500; margin-bottom: 2px; }}
.hero .sub {{ color: var(--ink-3); font-size: 14px; }}

.prog-wrap {{ margin: 4px 2px 16px; }}
.prog {{ height: 4px; background: var(--line-soft); border-radius: 2px; overflow: hidden; }}
.prog > div {{ height: 100%; background: var(--accent); transition: width .5s cubic-bezier(.2,0,0,1); }}
.prog-label {{ font-size: 12px; color: var(--ink-3); margin-top: 8px; display: flex; justify-content: space-between; }}

.card {{ background: var(--surface); border: 1px solid var(--line); border-radius: 8px; padding: 22px 24px;
         margin-bottom: 12px; color: var(--ink); }}
.card h3 {{ font-size: 18px; font-weight: 500; margin: 0 0 8px; padding: 0; color: var(--ink); }}
.card h3 + p, .card p {{ font-size: 15px; line-height: 1.6; color: var(--ink-2); margin: 0 0 8px; }}
.card li {{ font-size: 15px; line-height: 1.6; color: var(--ink-2); margin-bottom: 4px; }}
.card ul {{ margin: 6px 0 4px; padding-left: 20px; }}
.card .section {{ margin-top: 18px; }}
.card .muted {{ color: var(--ink-3); font-size: 13px; }}
.card a {{ color: var(--accent); }}

.chip {{ display: inline-flex; align-items: center; gap: 8px; font-size: 13px; font-weight: 500; color: var(--ink-2);
         border: 1px solid var(--line); border-radius: 8px; padding: 5px 12px; margin-bottom: 14px; background: var(--surface); }}
.chip .dot {{ width: 8px; height: 8px; border-radius: 50%; background: var(--accent); }}
.chip .dot.ai {{ background: #188038; }}

.summary {{ background: var(--page); border: 1px solid var(--line-soft); border-radius: 8px; padding: 16px 20px;
            font-size: 15px; line-height: 1.7; color: var(--ink); }}
.summary ul {{ margin: 0; padding-left: 20px; }}
.summary li {{ margin-bottom: 6px; color: var(--ink); }}
.notice {{ background: var(--tint); border-radius: 8px; padding: 12px 16px; color: #1f2a44; font-size: 14px;
           line-height: 1.5; margin-bottom: 12px; }}
.notice.pilot {{ background: #fef7e0; color: #5c4200; }}

.score {{ display: flex; gap: 12px; margin-top: 10px; }}
.score div {{ flex: 1; background: var(--page); border: 1px solid var(--line-soft); border-radius: 8px; padding: 16px; text-align: center; }}
.score b {{ display: block; font-size: 30px; font-weight: 400; color: var(--accent); }}
.score span {{ font-size: 13px; color: var(--ink-3); }}
.video-meta {{ font-size: 13px; color: var(--ink-3); margin: 6px 2px 14px; }}
iframe {{ border-radius: 8px; }}

/* forms and questions */
[data-testid="stForm"] {{ background: var(--surface); border: 1px solid var(--line) !important; border-radius: 8px; padding: 24px; }}
.form-title {{ font-size: 20px; font-weight: 400; color: var(--ink); margin: 0 0 4px; }}
.form-sub {{ font-size: 14px; color: var(--ink-3); margin: 0 0 6px; }}
.stRadio [data-testid="stWidgetLabel"] p, .stRadio > label p {{ font-weight: 500 !important; color: var(--ink); font-size: 15px; line-height: 1.5; }}
.stRadio [role="radiogroup"] label, .stCheckbox label {{ border-radius: 6px; padding: 5px 10px; margin: 1px 0;
  transition: background-color .15s ease; }}
.stRadio [role="radiogroup"] label:hover, .stCheckbox label:hover {{ background: #f1f3f4; }}
.stRadio [role="radiogroup"] p, .stCheckbox p {{ font-size: 14.5px; color: var(--ink-2); }}
.q-sep {{ border-top: 1px solid var(--line-soft); margin: 10px 0 16px; }}
.q-label {{ font-size: 15px; font-weight: 500; color: var(--ink); margin: 8px 0 2px; }}

/* buttons: flat at rest, elevation on hover, pressed on click */
.stButton > button, .stFormSubmitButton > button {{
  border-radius: 6px; font-weight: 500; letter-spacing: .01em; min-height: 44px; padding: .55rem 1.4rem;
  box-shadow: none; transition: box-shadow .2s ease, background-color .2s ease, transform .08s ease; }}
.stButton > button:hover, .stFormSubmitButton > button:hover {{ box-shadow: var(--shadow-1); background-color: var(--accent-hover);
  border-color: var(--accent-hover); color: #fff; }}
.stButton > button:active, .stFormSubmitButton > button:active {{ box-shadow: var(--shadow-2); transform: translateY(1px); }}
.stButton > button:focus-visible, .stFormSubmitButton > button:focus-visible {{ outline: 2px solid var(--accent); outline-offset: 2px; }}
[data-testid="stAlert"] {{ border-radius: 8px; }}
.foot {{ text-align: center; color: #80868b; font-size: 12px; margin-top: 28px; }}
</style>
""",
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------- state & helpers
@st.cache_data
def materials() -> dict:
    return load_materials()


@st.cache_resource
def store():
    return get_store(st.secrets)


M = materials()
ss = st.session_state


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def init_state() -> None:
    if "step" in ss:
        return
    ss.step = "consent"
    ss.page_start = time.time()
    ss.saved = False
    ss.save_error = None
    ss.scores = {}
    rec = empty_record()
    rec["participant_id"] = make_participant_id()
    rec["is_pilot"] = str(st.query_params.get("pilot", "")).lower() in ("1", "true", "yes")
    rec["app_version"] = APP_VERSION
    ss.rec = rec


def go(step: str) -> None:
    ss.step = step
    ss.page_start = time.time()


def elapsed() -> float:
    return time.time() - ss.page_start


def fmt(seconds: float) -> str:
    s = max(0, int(round(seconds)))
    return f"{s // 60}:{s % 60:02d}"


def prefix(part: str) -> str:
    return "p1" if part == "A" else "p2"


def method_of(part: str) -> str:
    return SEQUENCES[int(ss.rec["sequence"])][part]


def contact_paragraph() -> str:
    email = str(M.get("contact_email", "")).strip()
    return f'<p class="muted">Questions? Email <a href="mailto:{email}">{email}</a></p>' if email else ""


def contact_line() -> str:
    email = str(M.get("contact_email", "")).strip()
    return f" - Questions: <a href='mailto:{email}'>{email}</a>" if email else ""


def card(html: str) -> None:
    st.markdown(f'<div class="card">{html}</div>', unsafe_allow_html=True)


def header() -> None:
    st.markdown(
        f"""<div class="hero"><div class="kicker">AIPI 510 - Project 2</div>
        <h1>{M['study_title']}</h1>
        <div class="names">Alberto Gómez &amp; Colby Robbins</div>
        <div class="sub">Duke University - About 10 minutes</div></div>""",
        unsafe_allow_html=True,
    )
    i = STEPS.index(ss.step) if ss.step in STEPS else len(STEPS) - 1
    pct = int(100 * i / (len(STEPS) - 1))
    stage = {"A": "Part 1 of 2", "B": "Part 2 of 2"}.get(ss.step[0], "Getting started" if i < 3 else "Finished")
    st.markdown(
        f"""<div class="prog-wrap"><div class="prog"><div style="width:{pct}%"></div></div>
        <div class="prog-label"><span>{stage}</span><span>{pct}% complete</span></div></div>""",
        unsafe_allow_html=True,
    )
    if ss.rec["is_pilot"]:
        st.markdown('<div class="notice pilot"><b>Pilot mode.</b> Responses are flagged as pilot and excluded from the analysis.</div>',
                    unsafe_allow_html=True)


# ---------------------------------------------------------------- pages
def page_consent() -> None:
    missing = summaries_missing(M)
    if missing and not ss.rec["is_pilot"]:
        st.error("This study is not open yet. Please check back soon.")
        return
    if missing:
        st.warning(f"Setup incomplete: the ChatGPT summary is still a placeholder for {', '.join(missing)}.")
    card(
        f"""<h3>Welcome</h3>
        <p>We are two graduate students at Duke University studying <b>how different ways of studying affect what people remember</b>
        from a short educational video. Thank you for helping!</p>
        <h3 class="section">What you will do</h3>
        <ul><li>Watch a <b>4-minute video</b>, shown in two parts.</li>
        <li>For each part you will study in a different way (you will be told how).</li>
        <li>Answer <b>6 multiple-choice questions</b> after each part.</li></ul>
        <h3 class="section">Your privacy</h3>
        <ul><li>Participation is voluntary. You can stop at any time by closing this page.</li>
        <li>We do not collect your name, email or any identifying information. You get a random ID.</li>
        <li>Anonymous responses will be used for a student class project and shared publicly on GitHub.</li>
        <li>There are no risks beyond those of everyday life, and there is no compensation.</li></ul>
        {contact_paragraph()}"""
    )
    with st.form("consent"):
        agree = st.checkbox("I am 18 or older, I have read the information above, and I agree to take part.")
        if st.form_submit_button("Continue", type="primary", width="stretch"):
            if agree:
                go("background")
                st.rerun()
            st.error("Please confirm the statement above to continue.")


BACKGROUND_QUESTIONS = [
    ("taken_before_or_seen_video",
     "Have you done this study before (even partly), or already seen the TED-Ed video \"Meet the tardigrade\"?",
     ["No", "Yes"]),
    ("age_range", "What is your age range?", ["18-24", "25-34", "35-44", "45 or older"]),
    ("student_status", "Are you currently a student?",
     ["Yes, at Duke", "Yes, at another university", "No"]),
    ("native_english", "Is English your first language?", ["Yes", "No"]),
    ("device", "What device are you using right now?", ["Laptop or desktop computer", "Tablet", "Phone"]),
    ("usual_note_method", "How do you usually take notes in class or meetings?",
     ["By hand on paper", "On a laptop or tablet", "I use AI summaries", "I rarely take notes"]),
    ("ai_summary_use", "How often do you use AI tools (e.g., ChatGPT) to summarize content?",
     ["Never", "Rarely", "Monthly", "Weekly", "Daily"]),
    ("prior_knowledge", "Before today, how much did you know about tardigrades (\"water bears\")?",
     ["1 - Nothing", "2", "3", "4", "5 - A lot"]),
    ("attention_check", "To show you are reading carefully, please select \"Often\" below.",
     ["Never", "Rarely", "Sometimes", "Often", "Always"]),
]


def page_background() -> None:
    with st.form("background"):
        st.markdown('<div class="form-title">A few questions about you</div>', unsafe_allow_html=True)
        values = {}
        for i, (key, label, options) in enumerate(BACKGROUND_QUESTIONS):
            if i:
                st.markdown('<div class="q-sep"></div>', unsafe_allow_html=True)
            values[key] = st.radio(label, options, index=None, key=f"bg_{key}")
        if st.form_submit_button("Continue", type="primary", width="stretch"):
            if any(v is None for v in values.values()):
                st.error("Please answer every question.")
            else:
                for k, v in values.items():
                    ss.rec[k] = v.split(" -")[0] if k == "prior_knowledge" else v
                go("ineligible" if values["taken_before_or_seen_video"] == "Yes" else "setup")
                st.rerun()


def page_setup() -> None:
    card(
        """<h3>Before you start</h3>
        <ul><li>Have a <b>pen and a sheet of paper</b> ready.</li>
        <li>Turn your <b>sound on</b> (headphones are best). English captions are on by default (you can turn them off with the CC button).</li>
        <li>Find a quiet place and give the study your full attention for about 10 minutes.</li>
        <li>Watch each part <b>once, straight through</b>: please do not pause, rewind or rewatch it.</li>
        <li>Do not look anything up while you work.</li>
        <li>Please <b>do not refresh</b> this page, or you will have to start over.</li></ul>"""
    )
    if st.button("Begin the study", type="primary", width="stretch"):
        try:
            seq = choose_sequence(store().started_sequences())
            ss.rec["sequence"] = seq
            ss.rec["p1_method"] = SEQUENCES[seq]["A"]
            ss.rec["p2_method"] = SEQUENCES[seq]["B"]
            ss.rec["started_at"] = now_iso()
            store().log_allocation(ss.rec)  # logged before Part 1: balances starts, tracks drop-outs
        except Exception:  # storage unreachable: do not start a session we cannot save
            st.error("We could not connect to the study database. Please try again in a minute.")
            return
        go("A_watch")
        st.rerun()


def video_embed(part: str) -> None:
    p = M["parts"][part]
    vid = M["video"]["youtube_id"]
    src = (f"https://www.youtube-nocookie.com/embed/{vid}?start={p['start']}&end={p['end']}"
           "&rel=0&modestbranding=1&cc_load_policy=1&cc_lang_pref=en&hl=en&playsinline=1")
    html = f"""<div style="position:relative;padding-top:56.25%;border-radius:12px;overflow:hidden;background:#000">
        <iframe src="{src}" title="Study video" style="position:absolute;inset:0;width:100%;height:100%;border:0"
        allow="accelerometer; encrypted-media; picture-in-picture; fullscreen" allowfullscreen></iframe></div>"""
    if hasattr(st, "iframe"):  # Streamlit >= 1.5x
        st.iframe(html, height=405)
    else:
        components.html(html, height=405)
    st.markdown(
        f'<div class="video-meta">"{M["video"]["title"]}", {M["video"]["author"]} - '
        f'{p["label"]}: {fmt(p["start"])}–{fmt(p["end"])}</div>',
        unsafe_allow_html=True,
    )


def page_watch(part: str) -> None:
    method = method_of(part)
    label = M["parts"][part]["label"]
    if method == "handwritten":
        card(f"""<span class="chip"><span class="dot"></span>{label} - Handwritten notes</span>
            <h3>Take notes by hand while you watch</h3>
            <p>Press play and write down, on paper, whatever you think will help you answer questions later.
            You will have time to review your notes afterwards.</p>""")
    else:
        card(f"""<span class="chip"><span class="dot ai"></span>{label} - AI summary</span>
            <h3>Just watch: do not take any notes</h3>
            <p>Press play and pay attention. Put your pen down for this part.
            After the video you will read a summary of it written by ChatGPT.</p>""")
    video_embed(part)
    duration = M["parts"][part]["end"] - M["parts"][part]["start"]

    @st.fragment(run_every=1.0)
    def gate():
        remaining = duration + 2 - elapsed()
        if remaining > 0:
            st.caption(f"Press play now. The Continue button will appear once this part has had time to finish - {fmt(remaining)}")
        elif st.button("I've finished watching - Continue", type="primary", width="stretch", key=f"watched_{part}"):
            ss.rec[f"{prefix(part)}_watch_seconds"] = round(elapsed(), 1)
            go(f"{part}_review")
            st.rerun()

    gate()


def summary_html(text: str) -> str:
    """Show the ChatGPT output exactly as generated: '* ' / '- ' lines become a bulleted list."""
    from html import escape

    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if lines and all(ln[:2] in ("* ", "- ", "• ") for ln in lines):
        items = "".join(f"<li>{escape(ln[2:])}</li>" for ln in lines)
        return f'<ul style="margin:0;padding-left:20px">{items}</ul>'
    return "<br>".join(escape(ln) for ln in lines)


def finish_review(part: str, timed_out: bool) -> None:
    ss.rec[f"{prefix(part)}_review_seconds"] = REVIEW_MAX_SECONDS if timed_out else round(elapsed(), 1)
    ss.rec[f"{prefix(part)}_review_timed_out"] = timed_out
    go(f"{part}_quiz")


def page_review(part: str) -> None:
    method = method_of(part)
    label = M["parts"][part]["label"]
    if method == "handwritten":
        card(f"""<span class="chip"><span class="dot"></span>{label} - Review your notes</span>
            <h3>Review your handwritten notes</h3>
            <p>Read through your notes now. When you feel ready, start the quiz.
            You will <b>not</b> be able to look at your notes during the quiz.</p>""")
    else:
        summary = summary_html(M["parts"][part]["ai_summary"])
        card(f"""<span class="chip"><span class="dot ai"></span>{label} - Review the summary</span>
            <h3>Read the AI summary of this part</h3>
            <p class="muted">Generated by ChatGPT from the video's transcript.</p>
            <div class="summary">{summary}</div>
            <p style="margin-top:12px">When you feel ready, start the quiz. The summary will <b>not</b> be available during the quiz.</p>""")

    @st.fragment(run_every=1.0)
    def timer():
        left = REVIEW_MAX_SECONDS - elapsed()
        if left <= 0:
            finish_review(part, timed_out=True)
            st.rerun()
        st.caption(f"Take as long as you need, up to 2 minutes. The quiz starts automatically in {fmt(left)}.")

    timer()
    if method == "handwritten":
        st.markdown('<div class="notice"><b>Before you start the quiz,</b> put your notes away face down.</div>',
                    unsafe_allow_html=True)
    if st.button("I'm ready - Start the quiz", type="primary", width="stretch", key=f"ready_{part}"):
        finish_review(part, timed_out=False)
        st.rerun()


def honesty_items(method: str) -> list[tuple[str, str]]:
    """Self-reported deviations; each maps to one saved field (see page_quiz)."""
    method_items = ([("no_notes", "I did not take handwritten notes while watching")] if method == "handwritten" else
                    [("wrote_notes", "I wrote notes while watching or reading"),
                     ("no_summary", "I did not read the AI summary")])
    return method_items + [
        ("paused", "I paused, rewound, skipped ahead or changed the speed of the video"),
        ("looked", "I looked at notes, the summary or anything else while answering"),
        ("none", "None of these"),
    ]


def page_quiz(part: str) -> None:
    method = method_of(part)
    label = M["parts"][part]["label"]
    questions = M["questions"][part]
    p = prefix(part)
    if method == "handwritten":
        st.markdown('<div class="notice"><b>Keep your notes face down.</b> Please answer from memory.</div>',
                    unsafe_allow_html=True)
    else:
        st.markdown('<div class="notice"><b>The summary is no longer available.</b> Please answer from memory and keep any paper notes out of sight.</div>',
                    unsafe_allow_html=True)

    with st.form(f"quiz_{part}"):
        st.markdown(f'<div class="form-title">{label} quiz</div>'
                    '<div class="form-sub">Choose the best answer for each question.</div>', unsafe_allow_html=True)
        answers = {}
        for i, q in enumerate(questions, start=1):
            st.markdown('<div class="q-sep"></div>', unsafe_allow_html=True)
            answers[q["id"]] = st.radio(
                f"{i}. {q['text']}", list(q["options"]), index=None,
                format_func=lambda k, q=q: q["options"][k], key=f"{part}_{q['id']}",
            )
        st.markdown('<div class="q-sep"></div>', unsafe_allow_html=True)
        predicted = st.radio(
            f"How many of these {len(questions)} questions do you think you answered correctly?",
            list(range(len(questions) + 1)), index=None, horizontal=True, key=f"{part}_pred",
        )
        st.markdown('<div class="q-label">Quick honesty check: did any of these happen during this part?</div>'
                    '<div class="form-sub">Please be honest. It does not affect anything.</div>', unsafe_allow_html=True)
        checks = {k: st.checkbox(text, key=f"{part}_chk_{k}") for k, text in honesty_items(method)}
        if st.form_submit_button(f"Submit {label} answers", type="primary", width="stretch"):
            issues = [k for k, v in checks.items() if v and k != "none"]
            if any(v is None for v in [*answers.values(), predicted]):
                st.error("Please answer every question before submitting.")
                return
            if not issues and not checks["none"]:
                st.error("Please tick at least one box in the honesty check (or \"None of these\").")
                return
            if issues and checks["none"]:
                st.error("\"None of these\" cannot be combined with other boxes.")
                return
            compliance = "No" if ("no_notes" in issues or "no_summary" in issues) else "Yes"
            wrote_notes = ("Yes" if "wrote_notes" in issues else "No") if method == "ai" else "n/a"
            paused = "Yes" if "paused" in issues else "No"
            used = "Yes" if "looked" in issues else "No"
            ss.rec[f"{p}_quiz_seconds"] = round(elapsed(), 1)
            for i, q in enumerate(questions, start=1):
                ss.rec[f"{p}_q{i:02d}"] = answers[q["id"]]
            ss.rec[f"{p}_predicted_correct"] = predicted
            ss.rec[f"{p}_compliance"] = compliance
            ss.rec[f"{p}_ai_part_wrote_notes"] = wrote_notes
            ss.rec[f"{p}_paused_or_rewound"] = paused
            ss.rec[f"{p}_used_material_during_quiz"] = used
            ss.scores[part] = score_part(answers, questions)
            go("B_watch" if part == "A" else "done")
            st.rerun()


def page_ineligible() -> None:
    card("""<h3>Thank you for your interest!</h3>
        <p>To keep the results valid, each person can take part only once and the video has to be new to them,
        so we cannot include you this time.
        We really appreciate your help.</p>""")


def save_once() -> None:
    if ss.saved:
        return
    ss.rec["completed_at"] = now_iso()
    try:
        store().append(ss.rec)
        ss.saved, ss.save_error = True, None
    except Exception as exc:
        ss.save_error = str(exc)


def page_done() -> None:
    save_once()
    if ss.save_error:
        st.error("We could not save your responses yet. Please press the button below to try again. Do not close this page.")
        if st.button("Try saving again", type="primary"):
            st.rerun()
        return
    a, b = ss.scores.get("A", 0), ss.scores.get("B", 0)
    card(
        f"""<h3>Thank you! Your responses have been recorded.</h3>
        <p>Here is how you did:</p>
        <div class="score">
          <div><b>{a}/6</b><span>Part 1 - {METHOD_LABEL[method_of('A')]}</span></div>
          <div><b>{b}/6</b><span>Part 2 - {METHOD_LABEL[method_of('B')]}</span></div>
        </div>"""
    )
    card(
        f"""<h3>What was this study about?</h3>
        <p>We are comparing two ways of learning from a lecture video: <b>taking your own handwritten notes</b>
        versus <b>reading an AI-generated (ChatGPT) summary</b>. Everyone tries both methods, one per half of the
        video, in an order assigned at random so that neither half of the video favors one method.</p>
        <p><b>Please do not share the questions</b> with anyone who might still take part. Thank you!</p>
        <p class="muted">Your anonymous ID: <b>{ss.rec['participant_id']}</b>. Please write it down if you might want
        your responses removed later: contact Alberto Gómez or Colby Robbins{contact_line()} and mention this ID.</p>"""
    )


def scroll_to_top_on_new_step() -> None:
    """Streamlit keeps the scroll position between pages; jump to the top when the step changes."""
    if ss.get("_scrolled_for") == ss.step:
        return
    ss._scrolled_for = ss.step
    js = f"""<script>/* {ss.step} */
    const d = window.parent.document;
    d.querySelectorAll('[data-testid="stMain"], [data-testid="stAppViewContainer"], section.main')
     .forEach(e => e.scrollTo({{top: 0}}));
    window.parent.scrollTo({{top: 0}});
    </script>"""
    if hasattr(st, "iframe"):
        st.iframe(js, height=1)
    else:
        components.html(js, height=0)


# ---------------------------------------------------------------- router
init_state()
scroll_to_top_on_new_step()
header()
step = ss.step
if step == "consent":
    page_consent()
elif step == "background":
    page_background()
elif step == "setup":
    page_setup()
elif step.endswith("_watch"):
    page_watch(step[0])
elif step.endswith("_review"):
    page_review(step[0])
elif step.endswith("_quiz"):
    page_quiz(step[0])
elif step == "ineligible":
    page_ineligible()
else:
    page_done()
st.markdown('<div class="foot">AIPI 510 - Project 2 - Responses are anonymous</div>',
            unsafe_allow_html=True)
