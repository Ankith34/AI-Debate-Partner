# 🗣️ AI Debate Partner

Debate any topic against Google Gemini. Pick FOR or AGAINST, Gemini takes the opposite side, and when you click **End Debate** it evaluates your arguments.

**Stack:** Python, Streamlit, `google-genai` SDK.

## Run locally
```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # Windows: copy .env.example .env
# edit .env and paste your Gemini API key
streamlit run app.py
```
Get a free key at https://aistudio.google.com/apikey

## Deploy on Streamlit Community Cloud (free)
1. Push to GitHub:
   ```bash
   git init
   git add .
   git commit -m "AI Debate Partner"
   git branch -M main
   git remote add origin https://github.com/<your-username>/ai-debate-partner.git
   git push -u origin main
   ```
   (Create the empty repo on github.com first. `.env` is git-ignored, so your key is never pushed.)
2. Go to https://share.streamlit.io and sign in with GitHub.
3. Click **Create app** → choose your repo, branch `main`, main file `app.py`.
4. Open **Advanced settings → Secrets** and paste:
   ```toml
   GEMINI_API_KEY = "your_api_key_here"
   ```
5. Click **Deploy**. Your app gets a public `*.streamlit.app` URL.

## How it works
- `st.session_state` stores the topic, side and chat history between reruns.
- Each turn, the full history is sent to Gemini with a system instruction telling it which side to defend.
- **End Debate** sends the transcript with a "judge" prompt to produce the evaluation.
