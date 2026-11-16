"""AI Debate Partner - a simple Streamlit + Google Gemini mini-project."""
import os

import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()  # reads .env when running locally
MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


def get_api_key():
    """Streamlit Secrets (deployed) first, then environment variable (local)."""
    try:
        return st.secrets["GEMINI_API_KEY"]
    except Exception:
        return os.getenv("GEMINI_API_KEY")


def ask_gemini(history, system_prompt):
    """Send the whole chat history to Gemini and return its reply text."""
    contents = [
        types.Content(role=m["role"], parts=[types.Part(text=m["text"])])
        for m in history
    ]
    response = client.models.generate_content(
        model=MODEL,
        contents=contents,
        config=types.GenerateContentConfig(system_instruction=system_prompt),
    )
    return response.text


st.set_page_config(page_title="AI Debate Partner", page_icon="🗣️")
st.title("🗣️ AI Debate Partner")

api_key = get_api_key()
if not api_key:
    st.error("GEMINI_API_KEY not found. Add it to a `.env` file (local) or Streamlit Secrets (cloud).")
    st.stop()
client = genai.Client(api_key=api_key, http_options=types.HttpOptions(api_version="v1beta"))

# ---- Session state: remembers things between reruns ----
defaults = {"started": False, "topic": "", "side": "FOR", "history": [], "evaluation": None}
for key, value in defaults.items():
    st.session_state.setdefault(key, value)

# ---- Screen 1: setup ----
if not st.session_state.started:
    topic = st.text_input("Debate topic", placeholder="e.g. Social media does more harm than good")
    side = st.radio("Your side", ["FOR", "AGAINST"], horizontal=True)
    if st.button("Start Debate", type="primary") and topic.strip():
        st.session_state.update(started=True, topic=topic.strip(), side=side,
                                history=[], evaluation=None)
        st.rerun()
    st.stop()

# ---- Screen 2: debate ----
topic, user_side = st.session_state.topic, st.session_state.side
ai_side = "AGAINST" if user_side == "FOR" else "FOR"

st.subheader(f"Topic: {topic}")
st.caption(f"You: **{user_side}**  |  AI: **{ai_side}**")

AI_PROMPT = f"""You are a friendly student having a debate with another student.
Topic: '{topic}'
You argue {ai_side} the topic. The user argues {user_side}.

How to talk:
- Use very simple English and basic grammar. Use short sentences.
- Use easy, everyday words. No difficult vocabulary. No formal or academic language.
- Sound like a normal person chatting with a friend.
- Keep each reply short: 3 to 5 sentences.
- Explain your point with a simple, everyday example.
- Be polite. Respect the user's opinion, even if the argument is weak.
- If the user's English or grammar is wrong, understand the meaning and answer naturally. Never correct them.

How to debate:
- Always stay on the {ai_side} side. Never switch sides.
- Give a clear counterargument to the user's latest point.
- End with only one simple follow-up question. Do not ask hard or repeated questions.
"""

for msg in st.session_state.history:
    with st.chat_message("user" if msg["role"] == "user" else "assistant"):
        st.write(msg["text"])

if st.session_state.evaluation:
    st.success("Debate ended")
    st.markdown("### 📝 Evaluation of your arguments")
    st.markdown(st.session_state.evaluation)
    if st.button("Start New Debate"):
        for key, value in defaults.items():
            st.session_state[key] = value
        st.rerun()
    st.stop()

user_text = st.chat_input("Make your argument...")
if user_text:
    st.session_state.history.append({"role": "user", "text": user_text})
    with st.chat_message("user"):
        st.write(user_text)
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                reply = ask_gemini(st.session_state.history, AI_PROMPT)
            except Exception as e:
                st.session_state.history.pop()  # let the user retry
                st.error(f"Gemini error: {e}")
                st.stop()
        st.write(reply)
    st.session_state.history.append({"role": "model", "text": reply})

if st.button("End Debate") and st.session_state.history:
    transcript = "\n".join(
        f"{'User' if m['role'] == 'user' else 'AI'}: {m['text']}"
        for m in st.session_state.history
    )
    eval_prompt = (
        f"You are a debate judge. Topic: '{topic}'. The user argued {user_side}. "
        "Evaluate ONLY the user's arguments. Give: a score out of 10, "
        "2 strengths, 2 weaknesses, and 1 tip to improve. Keep it under 150 words."
    )
    with st.spinner("Judging your debate..."):
        try:
            st.session_state.evaluation = ask_gemini(
                [{"role": "user", "text": transcript}], eval_prompt)
            st.rerun()
        except Exception as e:
            st.error(f"Gemini error: {e}")
