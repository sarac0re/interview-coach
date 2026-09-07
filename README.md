# 🎙️ AI Interview Coach

A live, adaptive mock-interview web app. Pick a role and experience level, and it interviews you one question at a time — scoring each answer with specific, honest feedback instead of leaving you guessing.

**🔗 Live demo:** _add your Streamlit link here once deployed_

---

## Why

Most interview prep is a static list of questions with no feedback loop. This app closes that loop: every question adapts to what you've already answered, and every answer gets scored with concrete notes on what worked and what to fix — before the real interview, not during it.

## Features

- **Adaptive questioning** — questions are generated live by an LLM based on role, seniority, and everything you've answered so far, so nothing repeats
- **Real scoring, not just a transcript** — each answer gets a 1–10 score, named strengths, specific improvements, and a coach's tip
- **Voice or text answers** — practice speaking out loud with built-in speech-to-text, or type if you prefer
- **Session report** — a final breakdown across all questions with an overall score
- **Deployed live** — a real hosted app, not a local-only script

## Tech stack

| Layer | Tool |
|---|---|
| UI / app framework | [Streamlit](https://streamlit.io) |
| LLM | Llama 3.3 70B via [Groq API](https://console.groq.com) |
| Speech-to-text | `SpeechRecognition` + `streamlit-mic-recorder` |
| Hosting | Streamlit Community Cloud |

## How it works

1. You choose a role (e.g. Data Scientist), an experience level, and how many questions you want.
2. The app prompts the LLM for one interview question at a time, passing in the full Q&A history so far so each new question stays fresh and relevant.
3. You answer by typing or recording your voice.
4. Your answer is sent back to the LLM with a scoring prompt, which returns a structured JSON verdict: score, strengths, improvements, and a tip.
5. After the last question, you get a full session report with an overall score.

The LLM is prompted to return **strict JSON** for every question and every evaluation, which is what makes it possible to reliably drive the UI (scores, progress bars, structured feedback) instead of just printing free-form text.

## Running it yourself

**1. Get a free Groq API key**
→ [console.groq.com/keys](https://console.groq.com/keys) (no credit card needed)

**2. Clone this repo and install dependencies**
```bash
pip install -r requirements.txt
