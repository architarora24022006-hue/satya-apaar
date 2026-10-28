import os
import sys
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), '..')))

from app.main import app
from app.core.database import SessionLocal
from app.models.batch import UploadBatch
from app.models.case import Case

client = TestClient(app)

def test_sentinel_autonomous_batch_triage():
    # 1. Fetch latest batch
    db = SessionLocal()
    batch = db.query(UploadBatch).order_by(UploadBatch.created_at.desc()).first()
    batch_id = str(batch.id) if batch else "non_existent_fallback"
    db.close()

    # 2. Run autonomous triage
    res = client.post("/api/v1/sentinel/triage-batch", json={"batch_id": batch_id})
    assert res.status_code == 200
    data = res.json()

    assert data["success"] is True
    assert "thought_log" in data
    assert len(data["thought_log"]) >= 3
    # Check that thoughts have phase, timestamp, and message
    for t in data["thought_log"]:
        assert "phase" in t
        assert "timestamp" in t
        assert "message" in t

    assert "tool_executions" in data
    assert len(data["tool_executions"]) >= 1
    assert "executive_summary" in data
    assert len(data["executive_summary"]) > 10

def test_sentinel_chat_anomalies():
    # 1. Ask about Balaji College
    res1 = client.post("/api/v1/sentinel/chat", json={
        "message": "Why was Balaji College flagged by the system?"
    })
    assert res1.status_code == 200
    data1 = res1.json()
    assert "Balaji" in data1["answer"]
    assert "Anomaly Score" in data1["answer"]
    assert len(data1["tools_called"]) > 0

    # 2. Ask about seat capacity breach
    res2 = client.post("/api/v1/sentinel/chat", json={
        "message": "Which colleges are breaching approved seat capacity?"
    })
    assert res2.status_code == 200
    data2 = res2.json()
    assert "Seat Saturation" in data2["answer"] or "Breached" in data2["answer"]
    assert len(data2["tools_called"]) > 0

    # 3. Ask about trust score formula
    res3 = client.post("/api/v1/sentinel/chat", json={
        "message": "Explain how the Institution Trust Score is calculated"
    })
    assert res3.status_code == 200
    data3 = res3.json()
    assert "Data Quality" in data3["answer"]
    assert "Timeliness" in data3["answer"]
    assert "Anomaly Clearance" in data3["answer"]

def test_sentinel_human_approval_flow():
    # 1. Ensure at least one pending approval exists
    db = SessionLocal()
    pending = db.query(Case).filter(Case.status == "PENDING_APPROVAL").first()
    if not pending:
        # Create a pending approval case
        from datetime import datetime, timezone, timedelta
        inst = db.query(UploadBatch).first()
        inst_id = str(inst.institution_id) if inst else "dummy_inst"
        pending = Case(
            case_number="APPR-TEST-0001",
            title="APPROVAL REQUIRED: FREEZE_SEATS for Testing",
            institution_id=inst_id,
            status="PENDING_APPROVAL",
            priority="URGENT",
            sla_deadline=datetime.now(timezone.utc) + timedelta(hours=24),
            opened_by_type="SENTINEL",
            description="Automated intake breach detected by Sentinel Agent.",
            action_draft="Freeze admission intake for Computer Science branch.",
            evidence_pack={"action_type": "FREEZE_SEATS"}
        )
        db.add(pending)
        db.commit()
        db.refresh(pending)
    case_id = str(pending.id)
    db.close()

    # 2. Fetch pending approvals list
    list_res = client.get("/api/v1/sentinel/pending-approvals")
    assert list_res.status_code == 200
    approvals = list_res.json()
    assert len(approvals) > 0
    assert any(a["case_id"] == case_id for a in approvals)

    # 3. Officer approves action
    decide_res = client.post("/api/v1/sentinel/decide-approval", json={
        "case_id": case_id,
        "decision": "APPROVE",
        "officer_notes": "Confirmed breach in audit session. Authorizing seat lock."
    })
    assert decide_res.status_code == 200
    decide_data = decide_res.json()
    assert decide_data["success"] is True
    assert decide_data["decision"] == "APPROVE"

    # 4. Check case status is now RESOLVED
    db = SessionLocal()
    updated_case = db.query(Case).filter(Case.id == case_id).first()
    assert updated_case.status == "RESOLVED"
    assert "APPROVED BY HUMAN OFFICER" in updated_case.resolution_notes
    db.close()
