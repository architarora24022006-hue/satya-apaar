import os
import sys
import pytest
from fastapi.testclient import TestClient

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), '..')))

from app.main import app
from app.core.security import verify_claim_signature, get_public_key_b64, sign_claim

client = TestClient(app)

def test_health_endpoint():
    res = client.get("/api/v1/health/")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ONLINE"
    assert "ed25519_public_key" in data

def test_auth_login_aicte_admin():
    res = client.post("/api/v1/auth/login", json={
        "email": "admin@aicte.gov.in",
        "password": "Password@123"
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["role"] == "AICTE_ADMIN"

def test_auth_login_institution_admin():
    res = client.post("/api/v1/auth/login", json={
        "email": "admin@iitd.ac.in",
        "password": "Password@123"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["role"] == "INSTITUTION_ADMIN"

def test_auth_login_student():
    res = client.post("/api/v1/auth/login", json={
        "email": "aarav.sharma@satya.gov.in",
        "password": "Password@123",
        "otp_code": "123456"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["role"] == "STUDENT"

def test_demo_users_list():
    res = client.get("/api/v1/auth/demo-users")
    assert res.status_code == 200
    roles = res.json()
    assert len(roles) == 6

def test_audit_chain_integrity_clean():
    res = client.get("/api/v1/audit/verify-integrity")
    assert res.status_code == 200
    data = res.json()
    assert data["chain_valid"] is True
    assert data["broken_at_sequence"] is None

def test_ed25519_signature_and_verification():
    sample_claim = {
        "apaar_id_masked": "XXXX-XXXX-3541",
        "program": "UG",
        "branch": "Computer Science & Engineering",
        "institution_name": "Indian Institute of Technology Delhi",
        "aicte_approved": True
    }
    sig = sign_claim(sample_claim)
    pub = get_public_key_b64()
    assert verify_claim_signature(sample_claim, sig, pub) is True

    # Mutated claim must fail verification
    mutated_claim = dict(sample_claim)
    mutated_claim["program"] = "PhD Fraudulent"
    assert verify_claim_signature(mutated_claim, sig, pub) is False

def test_institutions_stats():
    # Login as AICTE Admin
    login_res = client.post("/api/v1/auth/login", json={
        "email": "admin@aicte.gov.in",
        "password": "Password@123"
    })
    token = login_res.json()["access_token"]
    
    res = client.get("/api/v1/institutions/stats/overview", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["total_institutions"] >= 40
    assert data["total_actual_enrolment"] >= 5000
    assert len(data["state_stats"]) > 5
