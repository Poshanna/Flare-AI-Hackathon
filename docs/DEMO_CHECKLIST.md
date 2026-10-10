# ClaimPilot AI — 3-Minute Demo Checklist

## Before the demo

- [ ] Install dependencies and confirm `python -m pytest -q` passes.
- [ ] Set `GEMINI_API_KEY` in local `.env` and confirm the key is not staged (`git check-ignore -v .env`).
- [ ] Start the app with `python -m streamlit run app\main.py`.
- [ ] Use synthetic data only.

## Demo sequence

1. **Intake (20 seconds):** Show the three fictional documents: claim form, repair estimate, and incident report. Point out the sample scenario option or upload controls.
2. **AI extraction (35 seconds):** With Gemini enabled, click **Extract fields with Gemini**. Explain that Gemini proposes structured fields and that the results must be checked against the original documents.
3. **Policy retrieval (35 seconds):** Search for `coverage deductible exclusions` and click **Search policy with Gemini embeddings**. Open a retrieved clause and explain that scores rank relevance; they are not probabilities or coverage decisions.
4. **Validation (45 seconds):** Click **Run claims review**. Show that the incident report conflicts with the claim form and repair estimate on vehicle registration and incident date.
5. **Human review + audit (30 seconds):** Highlight the recommended human adjuster review and download the JSON review report.

## Suggested talk track

"ClaimPilot AI is an evidence-driven assistant for motor-claims triage. It combines Gemini structured extraction with semantic policy retrieval and deterministic cross-document checks. The goal is to reduce the time a reviewer spends locating key facts and inconsistencies—not to make an unattended claim decision. Every finding points back to the source documents, and the final judgment remains with a human adjuster."

## Claims to avoid

- Do not describe the prototype as detecting fraud or deciding coverage.
- Do not call embedding similarity a confidence probability.
- Do not claim live production integration, validated business impact, or enterprise scale; those have not been demonstrated by this MVP.
- Do not show the API key or use real policyholder documents.

## Screenshot inventory

- `screenshots/gemini-extraction-and-policy-search.png` — successful extraction and semantic retrieval interface.
- `screenshots/claim-review-results.png` — two synthetic discrepancies and human-review recommendation.
