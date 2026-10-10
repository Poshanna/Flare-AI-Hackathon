"""Core ClaimPilot AI workflow: deterministic demo implementation."""
from __future__ import annotations
import re
from dataclasses import dataclass, asdict
from datetime import date
from typing import Iterable

FIELD_PATTERNS = {
    "claimant_name": [r"(?:claimant|customer|insured)\s*name\s*[:=-]\s*([^\n,;]+)"],
    "policy_number": [r"policy\s*(?:number|no\.?|#)\s*[:=-]\s*([A-Z0-9-]+)"],
    "vehicle_registration": [r"(?:vehicle\s*(?:registration|reg(?:istration)?\s*no\.?|number)|registration\s*(?:number|no\.?))\s*[:=-]\s*([A-Z0-9 -]+)"],
    "incident_date": [r"(?:incident|accident|loss)\s*date\s*[:=-]\s*(\d{4}-\d{2}-\d{2}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4})"],
    "incident_location": [r"(?:incident|accident|loss)\s*location\s*[:=-]\s*([^\n,;]+)"],
}

@dataclass
class Finding:
    code: str
    severity: str
    title: str
    detail: str
    evidence: str = ""

    def to_dict(self):
        return asdict(self)


def extract_fields(text: str) -> dict:
    """Extract common fields using transparent patterns; values must be verified."""
    results = {}
    for field, patterns in FIELD_PATTERNS.items():
        value = None
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                value = match.group(1).strip().rstrip(" .")
                break
        results[field] = value or ""
    return results


def normalize(value: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", (value or "").upper())


def check_required_fields(fields: dict) -> list[Finding]:
    required = {
        "policy_number": "Policy number",
        "vehicle_registration": "Vehicle registration",
        "incident_date": "Incident date",
    }
    findings = []
    for key, label in required.items():
        if not fields.get(key):
            findings.append(Finding("MISSING_" + key.upper(), "medium", f"Missing {label}", f"No {label.lower()} was extracted. Verify the source documents or request the information."))
    return findings


def check_policy_period(fields: dict, policy_text: str) -> list[Finding]:
    """Demo rule: reads ISO dates from explicitly labelled policy-period fields."""
    findings = []
    start = re.search(r"coverage\s*start\s*[:=-]\s*(\d{4}-\d{2}-\d{2})", policy_text, re.I)
    end = re.search(r"coverage\s*end\s*[:=-]\s*(\d{4}-\d{2}-\d{2})", policy_text, re.I)
    loss = fields.get("incident_date", "")
    if not (start and end and loss):
        return findings
    try:
        loss_date = parse_date(loss)
        start_date, end_date = date.fromisoformat(start.group(1)), date.fromisoformat(end.group(1))
        if not start_date <= loss_date <= end_date:
            findings.append(Finding("LOSS_OUTSIDE_POLICY_PERIOD", "high", "Incident date outside stated coverage period", f"Incident date {loss_date.isoformat()} falls outside the policy period {start_date.isoformat()} to {end_date.isoformat()}. This is a review flag only; it is not a coverage decision.", evidence=f"Coverage start: {start.group(1)}; coverage end: {end.group(1)}"))
    except ValueError:
        findings.append(Finding("DATE_NEEDS_REVIEW", "medium", "Date could not be validated", f"The incident date '{loss}' could not be parsed reliably."))
    return findings


def parse_date(value: str) -> date:
    value = value.strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y", "%m-%d-%Y", "%d/%m/%y", "%m/%d/%y"):
        from datetime import datetime
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    raise ValueError(value)


def compare_documents(named_texts: dict[str, str]) -> list[Finding]:
    """Flag disagreements across documents without inferring fraud or intent."""
    fields_by_doc = {name: extract_fields(text) for name, text in named_texts.items()}
    findings = []
    for field in ("policy_number", "vehicle_registration", "incident_date"):
        values = [(name, fields[field]) for name, fields in fields_by_doc.items() if fields.get(field)]
        groups: dict[str, list[tuple[str, str]]] = {}
        for name, value in values:
            groups.setdefault(normalize(value), []).append((name, value))
        if len(groups) > 1:
            detail = "; ".join(f"{name}: {value}" for name, value in values)
            findings.append(Finding("CONFLICT_" + field.upper(), "high", f"Conflicting {field.replace('_', ' ')} values", f"Different values were found across submitted documents. A reviewer should verify the source records. Values: {detail}", evidence=detail))
    return findings


def retrieve_policy_clauses(query: str, policy_text: str, top_k: int = 3) -> list[dict]:
    """Small dependency-free lexical retrieval for demo; not semantic production RAG."""
    chunks = [c.strip() for c in re.split(r"\n\s*\n", policy_text) if c.strip()]
    query_terms = {t.lower() for t in re.findall(r"[A-Za-z0-9]+", query) if len(t) > 2}
    scored = []
    for i, chunk in enumerate(chunks, 1):
        terms = {t.lower() for t in re.findall(r"[A-Za-z0-9]+", chunk) if len(t) > 2}
        score = len(query_terms & terms)
        if score:
            scored.append({"section": i, "text": chunk, "score": score})
    return sorted(scored, key=lambda x: (-x["score"], x["section"]))[:top_k]


def build_review(fields: dict, policy_text: str, documents: dict[str, str]) -> dict:
    findings = check_required_fields(fields)
    findings += check_policy_period(fields, policy_text)
    findings += compare_documents(documents)
    return {
        "claim_fields": fields,
        "policy_evidence": retrieve_policy_clauses("coverage deductible exclusion claim incident vehicle", policy_text),
        "findings": [f.to_dict() for f in findings],
        "recommended_next_action": "Human adjuster review required" if findings else "Continue to human adjuster review",
        "decision_boundary": "This prototype does not approve, deny, price, or settle claims.",
    }
