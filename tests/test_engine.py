from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
from engine import extract_fields, check_required_fields, check_policy_period, compare_documents, retrieve_policy_clauses


def test_extract_fields():
    fields = extract_fields("Policy Number: POL-123\nVehicle Registration: TS09AB1234\nIncident Date: 2026-10-08")
    assert fields["policy_number"] == "POL-123"
    assert fields["vehicle_registration"] == "TS09AB1234"
    assert fields["incident_date"] == "2026-10-08"


def test_missing_required_fields():
    findings = check_required_fields({"policy_number": "", "vehicle_registration": "", "incident_date": ""})
    assert len(findings) == 3


def test_policy_period_flags_outside_date():
    findings = check_policy_period({"incident_date": "2025-12-31"}, "Coverage start: 2026-01-01\nCoverage end: 2026-12-31")
    assert any(f.code == "LOSS_OUTSIDE_POLICY_PERIOD" for f in findings)


def test_cross_document_conflict():
    docs = {"a": "Policy Number: P1\nVehicle Registration: TS09AB1234\nIncident Date: 2026-10-08", "b": "Policy Number: P1\nVehicle Registration: TS09AB1284\nIncident Date: 2026-10-07"}
    codes = {f.code for f in compare_documents(docs)}
    assert "CONFLICT_VEHICLE_REGISTRATION" in codes
    assert "CONFLICT_INCIDENT_DATE" in codes


def test_policy_retrieval_returns_relevant_chunk():
    text = "Coverage overview: accidental damage may be considered.\n\nDeductible: INR 5000 per eligible claim."
    results = retrieve_policy_clauses("deductible claim", text)
    assert results and "Deductible" in results[0]["text"]
