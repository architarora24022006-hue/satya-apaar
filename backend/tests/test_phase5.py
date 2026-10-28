import os
import sys
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), '..')))

from app.main import app
from app.core.database import SessionLocal
from app.models.institution import Institution, ProgramBranch
from app.models.case import Case

client = TestClient(app)

def test_ghost_student_anomaly_detection():
    response = client.get("/api/v1/ml/anomalies")
    assert response.status_code == 200
    anomalies = response.json()
    assert len(anomalies) > 0

    # Ensure structured schema with explainability
    for a in anomalies[:5]:
        assert "institution_id" in a
        assert "anomaly_score" in a
        assert 0.0 <= a["anomaly_score"] <= 100.0
        assert a["risk_tier"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        assert "explanation" in a
        assert len(a["explanation"]) > 5

    # Check that Balaji or Apex is caught by the detector
    flagged_names = [a["name"] for a in anomalies if a["risk_tier"] in ["HIGH", "CRITICAL"]]
    assert any("Balaji" in name or "Apex" in name for name in flagged_names)

def test_single_institution_anomaly_detail():
    db = SessionLocal()
    inst = db.query(Institution).filter(Institution.name.ilike("%Balaji%")).first()
    if not inst:
        inst = db.query(Institution).first()
    inst_id = str(inst.id)
    db.close()

    response = client.get(f"/api/v1/ml/anomalies/{inst_id}")
    assert response.status_code == 200
    detail = response.json()
    assert detail["institution_id"] == inst_id
    assert "sequentiality_ratio" in detail
    assert "last_day_clustering" in detail
    assert "category_entropy" in detail

def test_trust_score_engine():
    # 1. Fetch trust scores
    response = client.get("/api/v1/ml/trust-scores")
    assert response.status_code == 200
    scores = response.json()
    assert len(scores) > 0

    top = scores[0]
    assert "trust_score" in top
    assert 0.0 <= top["trust_score"] <= 100.0
    assert "breakdown" in top
    bd = top["breakdown"]
    assert "data_quality_pts" in bd
    assert "timeliness_pts" in bd
    assert "anomaly_pts" in bd
    assert "resolution_pts" in bd

    # 2. Recalculate endpoint
    recalc_res = client.post("/api/v1/ml/trust-scores/recalculate")
    assert recalc_res.status_code == 200
    recalc_data = recalc_res.json()
    assert recalc_data["success"] is True
    assert recalc_data["total_institutions_updated"] > 0

def test_fuzzy_duplicate_matcher_and_case_escalation():
    # 1. Query fuzzy duplicates
    response = client.get("/api/v1/ml/fuzzy-duplicates?similarity_threshold=70.0")
    assert response.status_code == 200
    matches = response.json()
    
    if matches:
        match = matches[0]
        assert "composite_score" in match
        assert match["composite_score"] >= 70.0
        assert "record_a" in match
        assert "record_b" in match
        assert match["record_a"]["institution_id"] != match["record_b"]["institution_id"]

        # 2. 1-Click Escalate to Dispute Case
        case_res = client.post("/api/v1/ml/fuzzy-duplicates/open-case", json={
            "candidate_id": match["candidate_id"],
            "record_a_id": match["record_a"]["id"],
            "record_b_id": match["record_b"]["id"],
            "reason": match["explanation"]
        })
        assert case_res.status_code == 200
        case_data = case_res.json()
        assert case_data["success"] is True
        assert "case_id" in case_data

def test_predictive_seat_forecaster_and_locking():
    # 1. Query seat forecast
    response = client.get("/api/v1/ml/seat-forecast?days_remaining=14")
    assert response.status_code == 200
    forecasts = response.json()
    assert len(forecasts) > 0

    first_branch = forecasts[0]
    assert "branch_id" in first_branch
    assert "approved_intake" in first_branch
    assert "current_enrolled" in first_branch
    assert "projected_final_enrolment" in first_branch
    assert "risk_status" in first_branch
    assert first_branch["risk_status"] in ["BREACHED", "HIGH_RISK_PROJECTED_BREACH", "NEAR_CAPACITY_WARNING", "STABLE"]

    # Check that Apex Rohtak is flagged
    breached_or_high_risk = [f for f in forecasts if f["risk_status"] in ["BREACHED", "HIGH_RISK_PROJECTED_BREACH"]]
    assert len(breached_or_high_risk) > 0

    # 2. Test Seat Lock Toggle
    target_branch_id = first_branch["branch_id"]
    current_lock = first_branch["is_locked"]

    lock_res = client.post("/api/v1/ml/seat-lock/toggle", json={
        "branch_id": target_branch_id,
        "lock_state": not current_lock
    })
    assert lock_res.status_code == 200
    assert lock_res.json()["is_locked"] == (not current_lock)

    # Revert lock state
    client.post("/api/v1/ml/seat-lock/toggle", json={
        "branch_id": target_branch_id,
        "lock_state": current_lock
    })
