import os
import sys
import pytest
from fastapi.testclient import TestClient

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), '..')))

from app.main import app
from app.core.database import SessionLocal
from app.models.institution import Institution

client = TestClient(app)

@pytest.fixture
def auth_headers():
    login_res = client.post("/api/v1/auth/login", json={
        "email": "admin@aicte.gov.in",
        "password": "Password@123"
    })
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_national_dashboard_analytics(auth_headers):
    res = client.get("/api/v1/analytics/national", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    
    # 1. Summary stats
    assert "summary" in data
    assert data["summary"]["total_institutions"] >= 40
    assert data["summary"]["total_actual_enrolment"] >= 5000

    # 2. State Heatmap
    assert "state_heatmap" in data
    assert len(data["state_heatmap"]) >= 15
    haryana_state = next((s for s in data["state_heatmap"] if s["name"] == "Haryana"), None)
    assert haryana_state is not None
    # Apex Institute Rohtak is planted with over intake in Haryana
    assert haryana_state["risk_level"] == "BREACH"

    # 3. Category distribution
    assert "category_distribution" in data
    assert len(data["category_distribution"]) >= 4

    # 4. Flagged Radar
    assert "flagged_radar" in data
    assert len(data["flagged_radar"]) > 0

    # 5. Live Alert Feed
    assert "alerts_feed" in data

def test_institution_dashboard_analytics(auth_headers):
    db = SessionLocal()
    try:
        inst = db.query(Institution).filter(Institution.code == "IITD").first()
        inst_id = str(inst.id)
    finally:
        db.close()

    res = client.get(f"/api/v1/analytics/institution/{inst_id}", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()

    # Institution info
    assert data["institution"]["code"] == "IITD"
    assert data["institution"]["trust_score"] >= 60.0


    # Branch utilization & lock status
    assert "branch_utilization" in data
    assert len(data["branch_utilization"]) > 0
    assert all("lock_status" in b for b in data["branch_utilization"])

    # Trust score breakdown
    assert "trust_score_breakdown" in data
    assert "data_quality_factor" in data["trust_score_breakdown"]

def test_sse_endpoint_liveness():
    with client.stream("GET", "/api/v1/realtime/sse") as response:
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]
