from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime, timezone
import streamlit as st
from engine import extract_fields, build_review, retrieve_policy_clauses
from ai_services import (
    extract_fields_gemini, gemini_available, gemini_config,
    retrieve_policy_semantic,
)

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_DIR = ROOT / "data" / "sample_claim"
SAMPLE_POLICY = SAMPLE_DIR / "sample_policy.txt"

st.set_page_config(page_title="ClaimPilot AI", page_icon="🛡️", layout="wide")
st.title("🛡️ ClaimPilot AI")
st.caption("Evidence-driven insurance claims triage · Hackathon prototype · Synthetic data only")
st.warning("Decision-support demo only. Findings are review signals, not coverage decisions or fraud determinations.")

with st.sidebar:
    st.header("Workflow")
    st.markdown("1. Upload claim documents\n2. Extract structured fields\n3. Validate configured rules\n4. Review evidence and findings")
    use_sample = st.toggle("Load sample scenario", value=True)
    st.divider()
    ai_ready = gemini_available()
    use_gemini = st.toggle("Use Gemini AI features", value=ai_ready, help="Uses your local .env key for structured extraction and semantic policy retrieval.")
    if use_gemini and not ai_ready:
        st.warning("Gemini key not detected. Add GEMINI_API_KEY to your local .env file and restart Streamlit.")
    elif use_gemini:
        st.success(f"Gemini configured · {gemini_config()['model']}")
    else:
        st.caption("Local fallback mode: pattern extraction and keyword policy search.")
    st.caption("AI results must be verified against source documents. API errors fall back to local methods.")

policy_text = SAMPLE_POLICY.read_text(encoding="utf-8") if SAMPLE_POLICY.exists() else ""
if use_sample:
    claim_text = (SAMPLE_DIR / "claim_form.txt").read_text(encoding="utf-8")
    documents = {
        "claim_form.txt": claim_text,
        "repair_estimate.txt": (SAMPLE_DIR / "repair_estimate.txt").read_text(encoding="utf-8"),
        "incident_report.txt": (SAMPLE_DIR / "incident_report.txt").read_text(encoding="utf-8"),
    }
else:
    uploads = st.file_uploader("Upload claim documents (.txt, .pdf, .docx)", type=["txt", "pdf", "docx"], accept_multiple_files=True)
    claim_text = st.text_area("Incident description / claim notes", height=140, placeholder="Describe the reported incident and available claim details...")
    documents = {"claim_notes.txt": claim_text} if claim_text.strip() else {}
    if uploads:
        for file in uploads:
            try:
                if file.name.lower().endswith(".txt"):
                    content = file.getvalue().decode("utf-8", errors="replace")
                elif file.name.lower().endswith(".pdf"):
                    import fitz
                    doc = fitz.open(stream=file.getvalue(), filetype="pdf")
                    content = "\n".join(page.get_text() for page in doc)
                else:
                    from docx import Document
                    import io
                    doc = Document(io.BytesIO(file.getvalue()))
                    content = "\n".join(p.text for p in doc.paragraphs)
                documents[file.name] = content
            except Exception as exc:
                st.error(f"Could not read {file.name}: {type(exc).__name__}")

policy_upload = st.file_uploader("Optional: replace sample policy document (.txt)", type=["txt"], key="policy")
if policy_upload:
    policy_text = policy_upload.getvalue().decode("utf-8", errors="replace")

if not documents:
    st.info("Load the sample scenario or upload at least one document to begin.")
    st.stop()

all_text = "\n\n".join(documents.values())
local_fields = extract_fields(all_text)
if "gemini_fields" not in st.session_state:
    st.session_state["gemini_fields"] = {}
if "extraction_status" not in st.session_state:
    st.session_state["extraction_status"] = "Local pattern-based extraction is active."

left, right = st.columns([1, 1])
with left:
    st.subheader("Extracted claim information")
    labels = {
        "claimant_name": "Claimant name", "policy_number": "Policy number",
        "vehicle_registration": "Vehicle registration", "incident_date": "Incident date",
        "incident_location": "Incident location"
    }
    # Use the last AI extraction only when it was made for the current document set.
    doc_signature = str(hash(all_text))
    if st.session_state.get("extraction_signature") != doc_signature:
        st.session_state["gemini_fields"] = {}
        st.session_state["extraction_signature"] = doc_signature
        st.session_state["extraction_status"] = "Local pattern-based extraction is active."
    if use_gemini and ai_ready:
        if st.button("Extract fields with Gemini", help="Calls the configured Gemini model once for the current documents."):
            fields_ai, status = extract_fields_gemini(documents, local_fields)
            st.session_state["gemini_fields"] = fields_ai
            st.session_state["extraction_status"] = status
            for field_key, field_value in fields_ai.items():
                st.session_state[f"field_{field_key}"] = field_value
            st.rerun()
    current_fields = st.session_state["gemini_fields"] or local_fields
    st.caption(st.session_state["extraction_status"])
    edited = {}
    for key, label in labels.items():
        edited[key] = st.text_input(label, value=current_fields.get(key, ""), key=f"field_{key}")
    st.caption("Extracted values are suggestions. Verify them against source documents.")
with right:
    st.subheader("Policy evidence")
    query = st.text_input("Search policy clauses", value="coverage deductible exclusions")
    if use_gemini and ai_ready:
        @st.cache_data(ttl=3600, show_spinner=False)
        def cached_semantic_search(query_text: str, policy_body: str, model_name: str):
            # model_name is included in the cache key; credentials are never displayed.
            return retrieve_policy_semantic(query_text, policy_body)
        if st.button("Search policy with Gemini embeddings"):
            with st.spinner("Embedding query and policy clauses..."):
                clauses, retrieval_status = cached_semantic_search(query, policy_text, gemini_config()["embedding_model"])
            st.session_state["policy_clauses"] = clauses
            st.session_state["policy_retrieval_status"] = retrieval_status
        clauses = st.session_state.get("policy_clauses", retrieve_policy_clauses(query, policy_text))
        st.caption(st.session_state.get("policy_retrieval_status", "Click the button to run semantic retrieval."))
    else:
        clauses = retrieve_policy_clauses(query, policy_text)
        st.caption("Keyword retrieval mode. Enable Gemini AI features for semantic embeddings.")
    if clauses:
        for clause in clauses:
            citation = clause.get("citation", f"Sample policy · section {clause['section']}")
            with st.expander(f"{citation} · score {clause['score']}"):
                st.write(clause["text"])
                st.caption(f"Retrieval method: {clause.get('retrieval_method', 'keyword matching')}")
    else:
        st.info("No matching policy text found. Do not infer coverage without evidence.")

if st.button("Run claims review", type="primary", use_container_width=True):
    review = build_review(edited, policy_text, documents)
    review["claim_fields"] = edited
    review["generated_at_utc"] = datetime.now(timezone.utc).isoformat()
    review["extraction_method"] = "Gemini" if st.session_state.get("gemini_fields") else "Local pattern-based"
    review["policy_retrieval_method"] = "Gemini semantic embeddings" if use_gemini and ai_ready else "Keyword matching"
    review["recommended_next_action"] = "Human adjuster review required" if review["findings"] else "Continue to human adjuster review"
    review["decision_boundary"] = "This prototype does not approve, deny, price, or settle claims."
    st.session_state["review"] = review
    st.session_state["review_json"] = json.dumps(review, indent=2)

if "review" in st.session_state:
    review = st.session_state["review"]
    st.divider()
    st.subheader("Claims review results")
    findings = review["findings"]
    a, b, c = st.columns(3)
    a.metric("Findings", len(findings))
    b.metric("High severity", sum(1 for f in findings if f["severity"] == "high"))
    c.metric("Documents reviewed", len(documents))
    if findings:
        for f in findings:
            with st.expander(f"{f['severity'].upper()} · {f['title']}", expanded=True):
                st.write(f["detail"])
                if f.get("evidence"):
                    st.caption("Evidence: " + f["evidence"])
    else:
        st.success("No configured validation findings were detected. Human review is still required.")
    st.info("Recommended next action: " + review["recommended_next_action"])
    st.caption(review["decision_boundary"])
    st.download_button("Download review JSON", st.session_state["review_json"], file_name="claimpilot_review.json", mime="application/json")
    st.download_button("Download audit snapshot", st.session_state["review_json"], file_name="claimpilot_audit_snapshot.json", mime="application/json")

with st.expander("Documents included in this review"):
    for name, text in documents.items():
        st.markdown(f"**{name}**")
        st.text(text[:5000] + ("…" if len(text) > 5000 else ""))
