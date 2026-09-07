"""
AI Interview Coach — Streamlit app (FREE version)
--------------------------------------------------
Uses Groq's free LLM API (no cost, no credit card) instead of a paid API,
so the whole thing can run for $0 — both to build and to host.

SETUP (one-time):
1. Get a free Groq API key: https://console.groq.com/keys (sign up, no card needed)
2. Push this folder (this file + requirements.txt) to a GitHub repo
3. Deploy free at https://share.streamlit.io (Streamlit Community Cloud):
   - New app -> pick your repo -> main file: interview_coach_streamlit.py
   - In "Advanced settings -> Secrets", paste:
        GROQ_API_KEY = "your-key-here"
   - Deploy. You get a real https://yourapp.streamlit.app link, free forever tier.

Run locally instead (also free):
    pip install -r requirements.txt
    export GROQ_API_KEY="your-key-here"
    streamlit run interview_coach_streamlit.py
"""

import os
import json
import streamlit as st
from groq import Groq

# Works both locally (env var) and on Streamlit Cloud (st.secrets)
API_KEY = os.environ.get("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY", "")
client = Groq(api_key=API_KEY)
MODEL = "llama-3.3-70b-versatile"  # free, fast, strong general model on Groq

st.set_page_config(page_title="AI Interview Coach", page_icon="🎙️", layout="centered")

st.markdown("""
<style>
.stApp { background-color: #0B0F1A; color: #ECE9E2; }
.stButton>button { background-color: #C9973F; color: #0B0F1A; font-weight: 600; border: none; }
.stTextArea textarea { background-color: #121A2E; color: #ECE9E2; border: 1px solid #232D45; }
</style>
""", unsafe_allow_html=True)

if not API_KEY:
    st.error("No GROQ_API_KEY found. Add it as an environment variable (local) or a Streamlit Secret (hosted).")
    st.stop()


def ask_llm(system_prompt: str, user_prompt: str) -> dict:
    """Call Groq's chat API and parse a strict-JSON response."""
    resp = client.chat.completions.create(
        model=MODEL,
        max_tokens=1000,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    text = resp.choices[0].message.content
    cleaned = text.replace("```json", "").replace("```", "").strip()
    return json.loads(cleaned)


def generate_question(role: str, level: str, history: list) -> dict:
    prior = "\n\n".join(
        f"Q{i+1}: {h['question']}\nAnswer: {h['answer']}" for i, h in enumerate(history)
    )
    system = (
        f'You are a senior interviewer for a "{role}" role at {level} level. '
        "Ask one focused question at a time (mix of technical, behavioral, situational). "
        "Never repeat a question. Respond with ONLY raw JSON, no other text: "
        '{"question": string, "type": "Technical"|"Behavioral"|"Situational"}'
    )
    user = (
        f"Interview so far:\n{prior}\n\nAsk the next question, different in focus from above."
        if history else "Ask the first question — approachable but with real signal."
    )
    return ask_llm(system, user)


def evaluate_answer(role: str, level: str, question: str, answer: str) -> dict:
    system = (
        f'You are an expert interview coach scoring one answer for a "{role}" role at {level} level. '
        "Be honest and specific, not flattering. Respond with ONLY raw JSON, no other text: "
        '{"score": number (1-10), "strengths": [string,string], '
        '"improvements": [string,string], "tip": string}'
    )
    user = f"Question: {question}\n\nCandidate's answer: {answer}\n\nEvaluate it."
    return ask_llm(system, user)


def recognize_audio(audio_bytes) -> str:
    """Transcribe recorded audio bytes to text using SpeechRecognition (free Google Web Speech API)."""
    import io
    import speech_recognition as sr
    recognizer = sr.Recognizer()
    with sr.AudioFile(io.BytesIO(audio_bytes)) as source:
        audio_data = recognizer.record(source)
    try:
        return recognizer.recognize_google(audio_data)
    except sr.UnknownValueError:
        return ""
    except sr.RequestError:
        return ""


# ---------------- Session state ----------------
defaults = dict(stage="setup", q_index=0, question="", q_type="", history=[], feedback=None)
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

st.title("🎙️ AI Interview Coach")

# ---------------- Setup ----------------
if st.session_state.stage == "setup":
    st.subheader("Set up your mock interview")
    role = st.selectbox(
        "Role",
        ["Software Engineer (Entry-Level)", "Data Scientist", "Machine Learning Engineer",
         "Product Manager", "Data Analyst", "Custom role"],
    )
    if role == "Custom role":
        role = st.text_input("Enter the role") or "the role"
    level = st.select_slider("Experience level", options=["Entry-Level", "Mid-Level", "Senior"])
    n_questions = st.select_slider("Number of questions", options=[3, 5, 7], value=5)

    if st.button("Start interview", use_container_width=True):
        st.session_state.role = role
        st.session_state.level = level
        st.session_state.n_questions = n_questions
        st.session_state.stage = "interview"
        st.session_state.q_index = 0
        st.session_state.history = []
        with st.spinner("Preparing your first question…"):
            q = generate_question(role, level, [])
        st.session_state.question = q["question"]
        st.session_state.q_type = q.get("type", "Technical")
        st.rerun()

# ---------------- Interview ----------------
elif st.session_state.stage == "interview":
    st.caption(f"Question {st.session_state.q_index + 1} / {st.session_state.n_questions} · {st.session_state.q_type}")
    st.markdown(f"### {st.session_state.question}")

    transcribed = ""
    try:
        from streamlit_mic_recorder import mic_recorder
        audio = mic_recorder(start_prompt="🎤 Record answer", stop_prompt="⏹ Stop", key="mic")
        if audio:
            with st.spinner("Transcribing…"):
                transcribed = recognize_audio(audio["bytes"])
    except ImportError:
        st.caption("Voice input needs `streamlit-mic-recorder` (see requirements.txt) — typing works either way.")

    answer = st.text_area("Your answer", value=transcribed, height=180, key=f"answer_{st.session_state.q_index}")

    if st.button("Submit answer", use_container_width=True, disabled=not answer.strip()):
        with st.spinner("Scoring your answer…"):
            fb = evaluate_answer(st.session_state.role, st.session_state.level, st.session_state.question, answer)
        st.session_state.history.append({"question": st.session_state.question, "answer": answer, **fb})
        st.session_state.feedback = fb
        st.session_state.stage = "feedback"
        st.rerun()

# ---------------- Feedback ----------------
elif st.session_state.stage == "feedback":
    fb = st.session_state.feedback
    st.metric("Score", f"{fb['score']}/10")
    st.markdown("**What worked**")
    for s in fb["strengths"]:
        st.markdown(f"- {s}")
    st.markdown("**Sharpen this**")
    for s in fb["improvements"]:
        st.markdown(f"- {s}")
    st.info(fb["tip"])

    is_last = st.session_state.q_index + 1 >= st.session_state.n_questions
    label = "See final report" if is_last else "Next question"
    if st.button(label, use_container_width=True):
        if is_last:
            st.session_state.stage = "summary"
        else:
            st.session_state.q_index += 1
            with st.spinner("Preparing your next question…"):
                q = generate_question(st.session_state.role, st.session_state.level, st.session_state.history)
            st.session_state.question = q["question"]
            st.session_state.q_type = q.get("type", "Technical")
            st.session_state.stage = "interview"
        st.rerun()

# ---------------- Summary ----------------
elif st.session_state.stage == "summary":
    scores = [h["score"] for h in st.session_state.history]
    avg = sum(scores) / len(scores) if scores else 0
    st.subheader(f"Overall score: {avg:.1f}/10")
    st.caption(f"{st.session_state.role} · {st.session_state.level} · {st.session_state.n_questions} questions")

    for i, h in enumerate(st.session_state.history):
        with st.expander(f"Q{i+1} — {h['score']}/10 — {h['question'][:60]}"):
            st.write(f"**Your answer:** {h['answer']}")
            st.write(f"**Tip:** {h['tip']}")

    if st.button("Run another mock interview", use_container_width=True):
        for k, v in defaults.items():
            st.session_state[k] = v
        st.rerun()
