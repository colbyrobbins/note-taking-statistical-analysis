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

st.set_page_config(page_title="Note-Taking & Learning Study · Duke", page_icon="📝", layout="centered")

NAVY = "#012169"
STEPS = ["consent", "background", "setup", "A_watch", "A_review", "A_quiz", "B_watch", "B_review", "B_quiz", "done"]
METHOD_LABEL = {"handwritten": "Handwritten notes", "ai": "AI summary"}

st.markdown(
    f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, .stApp, .stMarkdown, .stRadio, .stCheckbox, button, input, textarea {{
  font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;
}}
#MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"] {{ display: none !important; }}
header[data-testid="stHeader"] {{ background: transparent; height: 0; }}
.stApp {{ background: #f1f3f4; }}
.block-container {{ max-width: 760px; padding-top: 1.5rem !important; padding-bottom: 4rem; }}

.hero {{ background: #fff; border: 1px solid #dadce0; border-top: 10px solid {NAVY}; border-radius: 12px;
         padding: 22px 26px 18px; margin-bottom: 14px; }}
.hero .kicker {{ font-size: 12px; font-weight: 600; letter-spacing: .08em; color: {NAVY}; text-transform: uppercase; }}
.hero h1 {{ font-size: 28px; line-height: 1.2; font-weight: 600; color: #202124; margin: 6px 0 4px; padding: 0; }}
.hero .sub {{ color: #5f6368; font-size: 14px; }}

.prog-wrap {{ margin: 2px 4px 16px; }}
.prog {{ height: 6px; background: #e3e6ea; border-radius: 99px; overflow: hidden; }}
.prog > div {{ height: 100%; background: {NAVY}; border-radius: 99px; transition: width .4s ease; }}
.prog-label {{ font-size: 12px; color: #5f6368; margin-top: 6px; display: flex; justify-content: space-between; }}

.card {{ background: #fff; border: 1px solid #dadce0; border-radius: 12px; padding: 20px 24px; margin-bottom: 14px; color: #202124; }}
.card h3 {{ font-size: 18px; font-weight: 600; margin: 0 0 8px; padding: 0; color: #202124; }}
.card p, .card li {{ font-size: 15px; line-height: 1.6; color: #3c4043; }}
.card ul {{ margin: 6px 0 0 0; padding-left: 20px; }}
.card .muted {{ color: #5f6368; font-size: 13px; }}
.pill {{ display: inline-block; font-size: 12px; font-weight: 600; padding: 4px 10px; border-radius: 99px;
         background: #e8edf7; color: {NAVY}; margin-bottom: 10px; }}
.pill.ai {{ background: #e6f4ea; color: #137333; }}
.summary {{ background: #f8f9fa; border-left: 4px solid #137333; border-radius: 8px; padding: 14px 16px;
            font-size: 16px; line-height: 1.7; color: #202124; }}
.notice {{ background: #fef7e0; border: 1px solid #f9e2a7; border-radius: 10px; padding: 12px 16px; color: #5f4b00; font-size: 14px; margin-bottom: 14px; }}
.score {{ display: flex; gap: 12px; margin-top: 8px; }}
.score div {{ flex: 1; background: #f8f9fa; border-radius: 10px; padding: 14px; text-align: center; }}
.score b {{ display: block; font-size: 26px; color: {NAVY}; }}
.score span {{ font-size: 13px; color: #5f6368; }}
.video-meta {{ font-size: 13px; color: #5f6368; margin: 4px 2px 12px; }}

[data-testid="stForm"] {{ background: #fff; border: 1px solid #dadce0 !important; border-radius: 12px; padding: 22px 24px; }}
.stRadio > label p, .stRadio [data-testid="stWidgetLabel"] p {{ font-weight: 600 !important; color: #202124; font-size: 15px; line-height: 1.5; }}
.q-sep {{ border-top: 1px solid #eceef1; margin: 6px 0 14px; }}
.stButton > button, .stFormSubmitButton > button {{ border-radius: 8px; font-weight: 600; padding: .55rem 1.2rem; }}
.foot {{ text-align: center; color: #80868b; font-size: 12px; margin-top: 26px; }}
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


def card(html: str) -> None:
    st.markdown(f'<div class="card">{html}</div>', unsafe_allow_html=True)


def header() -> None:
    st.markdown(
        f"""<div class="hero"><div class="kicker">Duke University · AIPI 510 Research Study</div>
        <h1>{M['study_title']}</h1>
        <div class="sub">About 10 minutes · Anonymous · Voluntary</div></div>""",
        unsafe_allow_html=True,
    )
    i = STEPS.index(ss.step)
    pct = int(100 * i / (len(STEPS) - 1))
    stage = {"A": "Part 1 of 2", "B": "Part 2 of 2"}.get(ss.step[0], "Getting started" if i < 3 else "Finished")
    st.markdown(
        f"""<div class="prog-wrap"><div class="prog"><div style="width:{pct}%"></div></div>
        <div class="prog-label"><span>{stage}</span><span>{pct}% complete</span></div></div>""",
        unsafe_allow_html=True,
    )
    if ss.rec["is_pilot"]:
        st.info("Pilot mode: responses are flagged as pilot and excluded from the analysis.")


# ---------------------------------------------------------------- pages
def page_consent() -> None:
    missing = summaries_missing(M)
    if missing and not ss.rec["is_pilot"]:
        st.error("This study is not open yet. Please check back soon.")
        return
    if missing:
        st.warning(f"Setup incomplete: the ChatGPT summary is still a placeholder for {', '.join(missing)}.")
    card(
        """<h3>Welcome</h3>
        <p>We are two graduate students at Duke University studying <b>how different ways of studying affect what people remember</b>
        from a short educational video. Thank you for helping!</p>
        <h3 style="margin-top:14px">What you will do</h3>
        <ul><li>Watch a <b>4-minute video</b>, shown in two parts.</li>
        <li>For each part you will study in a different way (you will be told how).</li>
        <li>Answer <b>6 multiple-choice questions</b> after each part.</li></ul>
        <h3 style="margin-top:14px">Your privacy</h3>
        <ul><li>Participation is voluntary. You can stop at any time by closing this page.</li>
        <li>We do not collect your name, email or any identifying information. You get a random ID.</li>
        <li>Anonymous responses will be used for a class project and shared publicly on GitHub.</li></ul>
        <p class="muted" style="margin-top:12px">Researchers: Alberto Gómez &amp; Colby Robbins · AIPI 510, Duke University</p>"""
    )
    with st.form("consent"):
        agree = st.checkbox("I am 18 or older, I have read the information above, and I agree to take part.")
        if st.form_submit_button("Continue", type="primary", width="stretch"):
            if agree:
                go("background")
                st.rerun()
            st.error("Please confirm the statement above to continue.")


BACKGROUND_QUESTIONS = [
    ("student_status", "Are you currently a student?",
     ["Yes, at Duke", "Yes, at another university", "No"]),
    ("native_english", "Is English your first language?", ["Yes", "No"]),
    ("usual_note_method", "How do you usually take notes in class or meetings?",
     ["By hand on paper", "On a laptop or tablet", "I use AI summaries", "I rarely take notes"]),
    ("ai_summary_use", "How often do you use AI tools (e.g., ChatGPT) to summarize content?",
     ["Never", "Rarely", "Monthly", "Weekly", "Daily"]),
    ("prior_knowledge", "Before today, how much did you know about tardigrades (\"water bears\")?",
     ["1 · Nothing", "2", "3", "4", "5 · A lot"]),
    ("attention_check", "To show you are reading carefully, please select \"Often\" below.",
     ["Never", "Rarely", "Sometimes", "Often", "Always"]),
]


def page_background() -> None:
    with st.form("background"):
        st.markdown("#### A few questions about you")
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
                    ss.rec[k] = v.split(" ·")[0] if k == "prior_knowledge" else v
                go("setup")
                st.rerun()


def page_setup() -> None:
    card(
        """<h3>Before you start</h3>
        <ul><li>Have a <b>pen and a sheet of paper</b> ready.</li>
        <li>Turn your <b>sound on</b> (headphones are best). English captions are available in the player.</li>
        <li>Find a quiet place and give the study your full attention for about 10 minutes.</li>
        <li>Watch each part <b>once</b>, without pausing or rewinding, and do not look anything up.</li>
        <li>Please <b>do not refresh</b> this page, or you will have to start over.</li></ul>"""
    )
    if st.button("Begin the study", type="primary", width="stretch"):
        try:
            seq = choose_sequence(store().completed_sequences())
        except Exception as exc:  # storage unreachable: do not start a session we cannot save
            st.error(f"We could not connect to the study database. Please try again in a minute. ({exc})")
            return
        ss.rec["sequence"] = seq
        ss.rec["p1_method"] = SEQUENCES[seq]["A"]
        ss.rec["p2_method"] = SEQUENCES[seq]["B"]
        ss.rec["started_at"] = now_iso()
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
        f'<div class="video-meta">"{M["video"]["title"]}", {M["video"]["author"]} · '
        f'{p["label"]}: {fmt(p["start"])}–{fmt(p["end"])}</div>',
        unsafe_allow_html=True,
    )


def page_watch(part: str) -> None:
    method = method_of(part)
    label = M["parts"][part]["label"]
    if method == "handwritten":
        card(f"""<span class="pill">✍️ {label} · Handwritten notes</span>
            <h3>Take notes by hand while you watch</h3>
            <p>Press play and write down, on paper, whatever you think will help you answer questions later.
            You will have time to review your notes afterwards.</p>""")
    else:
        card(f"""<span class="pill ai">🤖 {label} · AI summary</span>
            <h3>Just watch: do not take any notes</h3>
            <p>Press play and pay attention. Put your pen down for this part.
            After the video you will read a summary of it written by ChatGPT.</p>""")
    video_embed(part)
    duration = M["parts"][part]["end"] - M["parts"][part]["start"]

    @st.fragment(run_every=1.0)
    def gate():
        remaining = duration + 2 - elapsed()
        if remaining > 0:
            st.caption(f"The Continue button will appear when this part ends · {fmt(remaining)}")
        elif st.button("I've finished watching · Continue", type="primary", width="stretch", key=f"watched_{part}"):
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
        card(f"""<span class="pill">✍️ {label} · Review</span>
            <h3>Review your handwritten notes</h3>
            <p>Read through your notes now. When you feel ready, start the quiz.
            You will <b>not</b> be able to look at your notes during the quiz.</p>""")
    else:
        summary = summary_html(M["parts"][part]["ai_summary"])
        card(f"""<span class="pill ai">🤖 {label} · Review</span>
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
    if st.button("I'm ready · Start the quiz", type="primary", width="stretch", key=f"ready_{part}"):
        finish_review(part, timed_out=False)
        st.rerun()


def page_quiz(part: str) -> None:
    method = method_of(part)
    label = M["parts"][part]["label"]
    questions = M["questions"][part]
    p = prefix(part)
    if method == "handwritten":
        st.markdown('<div class="notice">📄 <b>Turn your notes face down now.</b> Please answer from memory.</div>',
                    unsafe_allow_html=True)
    else:
        st.markdown('<div class="notice">🧠 The summary is no longer available. Please answer from memory.</div>',
                    unsafe_allow_html=True)

    with st.form(f"quiz_{part}"):
        st.markdown(f"#### {label} quiz")
        st.caption("Choose the best answer for each question.")
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
        compliance_q = ("While watching this part, did you take handwritten notes?" if method == "handwritten"
                        else "Did you read the AI summary before starting this quiz?")
        compliance = st.radio(compliance_q, ["Yes", "Partly", "No"], index=None, horizontal=True, key=f"{part}_comp")
        used = st.radio(
            "Did you look at your notes, the summary, or anything else while answering? (Please be honest; it does not affect anything.)",
            ["No", "Yes"], index=None, horizontal=True, key=f"{part}_used",
        )
        if st.form_submit_button(f"Submit {label} answers", type="primary", width="stretch"):
            if any(v is None for v in [*answers.values(), predicted, compliance, used]):
                st.error("Please answer every question before submitting.")
                return
            ss.rec[f"{p}_quiz_seconds"] = round(elapsed(), 1)
            for i, q in enumerate(questions, start=1):
                ss.rec[f"{p}_q{i:02d}"] = answers[q["id"]]
            ss.rec[f"{p}_predicted_correct"] = predicted
            ss.rec[f"{p}_compliance"] = compliance
            ss.rec[f"{p}_used_material_during_quiz"] = used
            ss.scores[part] = score_part(answers, questions)
            go("B_watch" if part == "A" else "done")
            st.rerun()


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
        st.error("We could not save your responses yet. Please press the button below to try again.")
        if st.button("Try saving again", type="primary"):
            st.rerun()
        return
    a, b = ss.scores.get("A", 0), ss.scores.get("B", 0)
    card(
        f"""<h3>Thank you! Your responses have been recorded.</h3>
        <p>Here is how you did:</p>
        <div class="score">
          <div><b>{a}/6</b><span>Part 1 · {METHOD_LABEL[method_of('A')]}</span></div>
          <div><b>{b}/6</b><span>Part 2 · {METHOD_LABEL[method_of('B')]}</span></div>
        </div>"""
    )
    card(
        f"""<h3>What was this study about?</h3>
        <p>We are comparing two ways of learning from a lecture video: <b>taking your own handwritten notes</b>
        versus <b>reading an AI-generated (ChatGPT) summary</b>. Everyone tries both methods, one per half of the
        video, in an order assigned at random so that neither half of the video favors one method.</p>
        <p><b>Please do not share the questions</b> with anyone who might still take part. Thank you!</p>
        <p class="muted">Your anonymous ID: <b>{ss.rec['participant_id']}</b>. If you want your responses removed,
        contact Alberto Gómez or Colby Robbins and mention this ID.</p>"""
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
else:
    page_done()
st.markdown('<div class="foot">Duke University · AIPI 510 Module Project 2 · Anonymous research study</div>',
            unsafe_allow_html=True)
