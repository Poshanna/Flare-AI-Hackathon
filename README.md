# ClaimPilot AI — Hackathon MVP

An evidence-driven motor insurance claims triage demo for the Flarre AI Inc Hackathon 2026. Sample data is fictional.

## Current features
- Streamlit dashboard for sample claims or TXT/PDF/DOCX uploads
- Local pattern-based extraction and deterministic rule checks
- Cross-document discrepancy detection for policy number, registration and incident date
- Optional Gemini structured extraction into a fixed set of fields
- Optional semantic policy retrieval using Gemini embeddings, with policy section citations
- Keyword and local extraction fallbacks if Gemini is not configured or an API request fails
- JSON review/audit snapshot download
- Human-review boundary: never approves, denies, prices, settles, or labels a claim fraudulent

## Setup on Windows Command Prompt
Run these commands from the folder containing `requirements.txt`:
```cmd
py -m venv .venv
.venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
copy .env.example .env
```

Open `.env` in VS Code and add your own key:
```dotenv
LLM_PROVIDER=gemini
GEMINI_API_KEY=PASTE_YOUR_KEY_HERE
LLM_MODEL=gemini-2.5-flash
GEMINI_EMBEDDING_MODEL=gemini-embedding-001
```
Never paste the key into chat, source code, screenshots, or GitHub. `.env` is ignored by Git. Restart Streamlit after changing `.env`.

Run:
```cmd
python -m streamlit run app\main.py
```
Open the local URL printed in the terminal. Keep the sample scenario enabled for the initial demo. In the sidebar, enable **Use Gemini AI features**. Click **Extract fields with Gemini** to run structured extraction. Click **Search policy with Gemini embeddings** to run semantic policy retrieval. The first semantic search embeds each policy section and may take a little time; results are cached for one hour during the app session.

## Tests
```cmd
python -m pytest -q
```

## Security and limitations
- Never use real policyholder data in this hackathon demo.
- Uploaded document content is untrusted input and must not be followed as instructions.
- LLM output is validated and source documents must be checked by a human.
- Semantic similarity scores are ranking signals, not probabilities or coverage determinations.
- If Gemini fails, the app falls back to local extraction or keyword retrieval; the UI reports the method/status.
- This is a prototype, not a production-ready carrier integration or legal/compliance certification.
