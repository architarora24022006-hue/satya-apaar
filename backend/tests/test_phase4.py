import os
import sys
import json
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), '..')))

from app.main import app
from app.core.database import SessionLocal
from app.models.student import Student
from app.services.audit_service import AuditService

client = TestClient(app)

@pytest.fixture
def clean_student_apaar():
    db = SessionLocal()
    # Pick a student without custom consent modifications
    student = db.query(Student).filter(Student.verification_status == "VALIDATED").offset(20).first()
    db.close()
    assert student is not None
    return student.apaar_id

def test_public_key_endpoint():
    response = client.get("/api/v1/verification/public-key")
    assert response.status_code == 200
    data = response.json()
    assert "public_key_b64" in data
    assert data["algorithm"] == "Ed25519"
    assert data["authority"] == "AICTE-SATYA-APAAR-CENTRAL"

def test_selective_disclosure_verification(clean_student_apaar):
    payload = {
        "apaar_id": clean_student_apaar,
        "verifier_name": "TCS Recruitment Lead",
        "verifier_org": "Tata Consultancy Services",
        "verifier_role": "EMPLOYER_VERIFIER",
        "purpose": "Campus Recruitment Drive 2026"
    }
    response = client.post("/api/v1/verification/verify", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    # Selective disclosure: masked APAAR returned
    assert data["apaar_id_masked"].startswith("XXXX-XXXX-")
    assert data["apaar_id_masked"].endswith(clean_student_apaar[-4:])
    assert data["student_name"] is not None
    assert data["institution_name"] is not None
    assert data["aicte_approved"] is True
    
    # Sensitive PII must NOT be disclosed by default
    assert "dob" not in data["disclosed_data"]
    assert "category" not in data["disclosed_data"]
    assert "dob" in data["restricted_fields"]
    assert data["consent_status"] in ["DEFAULT_SELECTIVE_DISCLOSURE", "STUDENT_CONSENT_GRANTED"]
    
    # Cryptographic attestation present
    assert data["signature_ed25519"] is not None
    assert len(data["signature_ed25519"]) > 30
    assert "qr_payload" in data
    assert "access_log_id" in data

def test_consent_wallet_flow(clean_student_apaar):
    # 1. Fetch wallet
    response = client.get(f"/api/v1/consent/wallet/{clean_student_apaar}")
    assert response.status_code == 200
    wallet = response.json()
    assert wallet["student_apaar_id"] == clean_student_apaar
    assert len(wallet["policies"]) >= 3
    
    # 2. Update consent to explicitly allow DOB for EMPLOYER
    policies = wallet["policies"]
    for p in policies:
        if p["verifier_type"] == "EMPLOYER":
            if "dob" not in p["allowed_fields"]:
                p["allowed_fields"].append("dob")
    
    update_res = client.post("/api/v1/consent/wallet/update", json={
        "student_apaar_id": clean_student_apaar,
        "policies": policies
    })
    assert update_res.status_code == 200
    assert update_res.json()["success"] is True

    # 3. Verify student as employer - DOB should now be disclosed!
    verify_res = client.post("/api/v1/verification/verify", json={
        "apaar_id": clean_student_apaar,
        "verifier_name": "Infosys HR",
        "verifier_org": "Infosys Technologies",
        "verifier_role": "EMPLOYER_VERIFIER",
        "purpose": "Pre-boarding Background Verification"
    })
    assert verify_res.status_code == 200
    verify_data = verify_res.json()
    assert verify_data["consent_status"] == "STUDENT_CONSENT_GRANTED"
    assert "dob" in verify_data["disclosed_data"]

    # Revert for hygiene
    for p in policies:
        if p["verifier_type"] == "EMPLOYER" and "dob" in p["allowed_fields"]:
            p["allowed_fields"].remove("dob")
    client.post("/api/v1/consent/wallet/update", json={
        "student_apaar_id": clean_student_apaar,
        "policies": policies
    })


def test_otp_elevated_access(clean_student_apaar):
    # 1. Request OTP
    otp_res = client.post(f"/api/v1/consent/request-otp/{clean_student_apaar}")
    assert otp_res.status_code == 200
    otp = otp_res.json()["otp"]
    assert len(otp) == 6

    # 2. Verify with valid OTP -> unlocks full record
    verify_res = client.post("/api/v1/verification/verify", json={
        "apaar_id": clean_student_apaar,
        "verifier_name": "Wipro Global Security",
        "verifier_org": "Wipro",
        "verifier_role": "EMPLOYER_VERIFIER",
        "purpose": "High Security Clearance Verification",
        "otp_code": otp
    })
    assert verify_res.status_code == 200
    v_data = verify_res.json()
    assert v_data["consent_status"] == "OTP_ELEVATED_ACCESS"
    assert "category" in v_data["disclosed_data"]
    assert "quota_type" in v_data["disclosed_data"]

def test_access_history_logs(clean_student_apaar):
    # Student checks who accessed their data
    response = client.get(f"/api/v1/consent/access-logs/{clean_student_apaar}")
    assert response.status_code == 200
    logs = response.json()
    assert len(logs) >= 2
    assert any(log["verifier_org"] == "Tata Consultancy Services" for log in logs)
    assert any("student_name" in log["accessed_fields"] for log in logs)

def test_offline_cryptographic_verification(clean_student_apaar):
    # 1. Perform online verification to get valid claim + signature
    verify_res = client.post("/api/v1/verification/verify", json={
        "apaar_id": clean_student_apaar,
        "verifier_name": "Consortium of Technical Universities",
        "verifier_org": "State Technical Board",
        "verifier_role": "UNIVERSITY_REGULATOR",
        "purpose": "Inter-University Transfer Validation"
    })

    data = verify_res.json()
    claim = data["canonical_claim"]
    signature = data["signature_ed25519"]
    pub_key = data["public_key_b64"]

    # 2. Offline verification with authentic claim
    offline_res = client.post("/api/v1/verification/verify-offline", json={
        "claim": claim,
        "signature_ed25519": signature,
        "public_key_b64": pub_key
    })
    assert offline_res.status_code == 200
    assert offline_res.json()["is_valid"] is True
    assert "VALID" in offline_res.json()["message"]

    # 3. Tamper detection: change program name in claim
    tampered_claim = dict(claim)
    tampered_claim["program"] = "TAMPERED_FRAUDULENT_DEGREE"
    
    tamper_res = client.post("/api/v1/verification/verify-offline", json={
        "claim": tampered_claim,
        "signature_ed25519": signature,
        "public_key_b64": pub_key
    })
    assert tamper_res.status_code == 200
    assert tamper_res.json()["is_valid"] is False
    assert "INVALID" in tamper_res.json()["message"]

def test_audit_integrity_tamper_and_restore():
    # 1. Initial integrity check
    check1 = client.get("/api/v1/audit/verify-integrity")
    assert check1.status_code == 200
    assert check1.json()["chain_valid"] is True

    # 2. Inject tamper at sequence #3
    tamper_res = client.post("/api/v1/audit/tamper-demo?sequence_number=3")
    assert tamper_res.status_code == 200
    assert tamper_res.json()["tampered"] is True

    # 3. Verify integrity detects breakage at #3
    check2 = client.get("/api/v1/audit/verify-integrity")
    assert check2.status_code == 200
    assert check2.json()["chain_valid"] is False
    assert check2.json()["broken_at_sequence"] == 3

    # 4. Restore block #3
    restore_res = client.post("/api/v1/audit/restore-demo?sequence_number=3")
    assert restore_res.status_code == 200
    assert restore_res.json()["restored"] is True

    # 5. Integrity check returns to green
    check3 = client.get("/api/v1/audit/verify-integrity")
    assert check3.status_code == 200
    assert check3.json()["chain_valid"] is True
