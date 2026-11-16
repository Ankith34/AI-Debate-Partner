"""AI Debate Partner - minimal Streamlit + Google Gemini mini-project."""
import os
import re

import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()  # reads .env when running locally
MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
EMOTIONS = ["happy", "excited", "thinking", "surprised", "sad", "angry", "neutral"]


# ---------- Mascot: a small original creature drawn with SVG ----------
def mascot(emotion):
    """Return an SVG of the mascot showing the given emotion."""
    dot = lambda x, y, r=6: f'<circle cx="{x}" cy="{y}" r="{r}" fill="#222"/>'
    stroke = 'fill="none" stroke="#222" stroke-width="4" stroke-linecap="round"'
    faces = {
        "happy": (f'<path d="M65 98 Q75 84 85 98" {stroke}/><path d="M115 98 Q125 84 135 98" {stroke}/>',
                  f'<path d="M86 116 Q100 134 114 116" {stroke}/>', ""),
        "excited": (dot(75, 95, 8) + dot(125, 95, 8),
                    '<path d="M84 114 Q100 146 116 114 Z" fill="#c0392b" stroke="#222" stroke-width="3"/>',
                    '<text x="160" y="50" font-size="24">✦</text><text x="30" y="60" font-size="18">✦</text>'),
        "surprised": ('<circle cx="75" cy="95" r="10" fill="#fff" stroke="#222" stroke-width="3"/>' + dot(75, 95, 4)
                      + '<circle cx="125" cy="95" r="10" fill="#fff" stroke="#222" stroke-width="3"/>' + dot(125, 95, 4),
                      '<ellipse cx="100" cy="124" rx="7" ry="9" fill="#222"/>', ""),
        "sad": (dot(75, 98) + dot(125, 98),
                f'<path d="M87 128 Q100 116 113 128" {stroke}/>',
                '<ellipse cx="68" cy="114" rx="4" ry="7" fill="#6ec1ff"/>'),
        "angry": (dot(75, 98) + dot(125, 98) + f'<path d="M60 80 L90 90" {stroke}/><path d="M140 80 L110 90" {stroke}/>',
                  f'<path d="M88 126 L112 126" {stroke}/>', ""),
        "thinking": (dot(80, 92) + dot(130, 92),
                     f'<path d="M92 124 Q100 121 108 126" {stroke}/>',
                     '<circle cx="165" cy="45" r="18" fill="#fff" stroke="#222" stroke-width="3"/>'
                     '<text x="158" y="53" font-size="22" font-weight="bold">?</text>'),
        "neutral": (dot(75, 98) + dot(125, 98), f'<path d="M90 120 Q100 128 110 120" {stroke}/>', ""),
    }
    eyes, mouth, extra = faces.get(emotion, faces["neutral"])
    return (
        '<div class="mascot"><svg width="170" height="170" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">'
        '<polygon points="60,70 40,15 90,50" fill="#FFD84D" stroke="#222" stroke-width="4"/>'
        '<polygon points="140,70 160,15 110,50" fill="#FFD84D" stroke="#222" stroke-width="4"/>'
        '<polygon points="40,15 49,35 35,30" fill="#222"/><polygon points="160,15 151,35 165,30" fill="#222"/>'
        '<ellipse cx="100" cy="115" rx="68" ry="60" fill="#FFD84D" stroke="#222" stroke-width="4"/>'
        '<circle cx="55" cy="118" r="10" fill="#FF7A7A"/><circle cx="145" cy="118" r="10" fill="#FF7A7A"/>'
        f'{eyes}{mouth}{extra}</svg></div>'
    )


STYLE = """<style>
#MainMenu, footer, header {visibility: hidden;}
.block-container {max-width: 700px; padding-top: 1.5rem;}
.mascot {text-align: center; animation: bob 2.5s ease-in-out infinite;}
@keyframes bob {0%,100% {transform: translateY(0);} 50% {transform: translateY(-6px);}}
h1, h3 {text-align: center; font-weight: 600;}
.caption {text-align: center; color: #888; margin-bottom: 1rem;}
</style>"""


# ---------- Gemini helpers ----------
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


def split_emotion(reply):
    """Turn '[happy] Hello!' into ('happy', 'Hello!')."""
    match = re.match(r"\s*\[(\w+)\]\s*", reply)
    if match and match.group(1).lower() in EMOTIONS:
        return match.group(1).lower(), reply[match.end():].strip()
    return "neutral", reply.strip()


# ---------- Page setup ----------
st.set_page_config(page_title="AI Debate Partner", page_icon="🗣️")
st.markdown(STYLE, unsafe_allow_html=True)

api_key = get_api_key()
if not api_key:
    st.error("GEMINI_API_KEY not found. Add it to a `.env` file (local) or Streamlit Secrets (cloud).")
    st.stop()
client = genai.Client(api_key=api_key, http_options=types.HttpOptions(api_version="v1beta"))

# ---- Session state: remembers things between reruns ----
defaults = {"started": False, "topic": "", "side": "FOR", "history": [],
            "evaluation": None, "emotion": "happy"}
for key, value in defaults.items():
    st.session_state.setdefault(key, value)

mascot_box = st.empty()  # the mascot lives here so we can change it any time
mascot_box.markdown(mascot(st.session_state.emotion), unsafe_allow_html=True)
st.markdown("<h1>AI Debate Partner</h1>", unsafe_allow_html=True)

# ---- Screen 1: setup ----
if not st.session_state.started:
    topic = st.text_input("Debate topic", placeholder="e.g. Social media does more harm than good")
    side = st.radio("Your side", ["FOR", "AGAINST"], horizontal=True)
    if st.button("Start Debate", type="primary", use_container_width=True) and topic.strip():
        st.session_state.update(started=True, topic=topic.strip(), side=side,
                                history=[], evaluation=None, emotion="excited")
        st.rerun()
    st.stop()

# ---- Screen 2: debate ----
topic, user_side = st.session_state.topic, st.session_state.side
ai_side = "AGAINST" if user_side == "FOR" else "FOR"

st.markdown(f"<div class='caption'>{topic}<br>You: <b>{user_side}</b> · AI: <b>{ai_side}</b></div>",
            unsafe_allow_html=True)

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

Emotion rule:
- Start every reply with exactly one emotion tag in square brackets, then your message.
- Choose the tag that fits how you feel: {", ".join(EMOTIONS)}.
- Example: [excited] Wow, good point! But I think...
"""

for msg in st.session_state.history:
    with st.chat_message("user" if msg["role"] == "user" else "assistant"):
        st.write(msg["text"])

if st.session_state.evaluation:
    st.markdown("### Evaluation")
    st.markdown(st.session_state.evaluation)
    if st.button("Start New Debate", use_container_width=True):
        for key, value in defaults.items():
            st.session_state[key] = value
        st.rerun()
    st.stop()

user_text = st.chat_input("Make your argument...")
if user_text:
    st.session_state.history.append({"role": "user", "text": user_text})
    with st.chat_message("user"):
        st.write(user_text)
    mascot_box.markdown(mascot("thinking"), unsafe_allow_html=True)
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                raw_reply = ask_gemini(st.session_state.history, AI_PROMPT)
            except Exception as e:
                st.session_state.history.pop()  # let the user retry
                st.error(f"Gemini error: {e}")
                st.stop()
        emotion, reply = split_emotion(raw_reply)
        st.write(reply)
    st.session_state.history.append({"role": "model", "text": reply})
    st.session_state.emotion = emotion
    mascot_box.markdown(mascot(emotion), unsafe_allow_html=True)

if st.button("End Debate", use_container_width=True) and st.session_state.history:
    transcript = "\n".join(
        f"{'User' if m['role'] == 'user' else 'AI'}: {m['text']}"
        for m in st.session_state.history
    )
    eval_prompt = (
        f"You are a debate judge. Topic: '{topic}'. The user argued {user_side}. "
        "Evaluate ONLY the user's arguments. Give: a score out of 10, "
        "2 strengths, 2 weaknesses, and 1 tip to improve. Keep it under 150 words."
    )
    mascot_box.markdown(mascot("thinking"), unsafe_allow_html=True)
    with st.spinner("Judging your debate..."):
        try:
            st.session_state.evaluation = ask_gemini(
                [{"role": "user", "text": transcript}], eval_prompt)
            st.session_state.emotion = "happy"
            st.rerun()
        except Exception as e:
            st.error(f"Gemini error: {e}")
