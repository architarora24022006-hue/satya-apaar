import os
import sys
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), '..')))

from app.main import app

client = TestClient(app)

def test_safe_nl_analytics_top_institutions():
    """Validates Safe NL Analytics allowlisted query plan for top institutions."""
    res = client.post("/api/v1/analytics/nl-query", json={
        "query": "Show me the top 5 institutions by enrollment"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["intent"] == "TOP_INSTITUTIONS_BY_ENROLMENT"
    assert "Rank" in data["columns"]
    assert "Institution Name" in data["columns"]
    assert len(data["rows"]) > 0
    assert "SELECT name" in data["sql_translation"]
    assert "summary_insight" in data

def test_safe_nl_analytics_risk_trust_scores():
    """Validates Safe NL Analytics allowlisted query plan for low trust institutions."""
    res = client.post("/api/v1/analytics/nl-query", json={
        "query": "List all colleges with trust score below 70"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["intent"] == "INSTITUTIONS_AT_RISK_TRUST"
    assert "Trust Score" in data["columns"]
    assert "SELECT aicte_id" in data["sql_translation"]

def test_safe_nl_analytics_demographics():
    """Validates Safe NL Analytics demographic distribution query plan."""
    res = client.post("/api/v1/analytics/nl-query", json={
        "query": "Show gender distribution across admitted students"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["intent"] == "DEMOGRAPHIC_DISTRIBUTION"
    assert data["chart_type"] == "PIE"
    assert len(data["rows"]) >= 2

def test_export_trust_scores_excel():
    """Validates generation and streaming of styled openpyxl Excel audit report."""
    res = client.get("/api/v1/export/trust-scores?format=excel")
    assert res.status_code == 200
    assert "application/vnd.openxmlformats" in res.headers["content-type"]
    assert "attachment; filename=AICTE_Trust_Score_Leaderboard.xlsx" in res.headers["content-disposition"]
    assert len(res.content) > 3000

def test_export_trust_scores_pdf():
    """Validates generation and streaming of official reportlab PDF compliance report."""
    res = client.get("/api/v1/export/trust-scores?format=pdf")
    assert res.status_code == 200
    assert "application/pdf" in res.headers["content-type"]
    assert "attachment; filename=AICTE_Trust_Score_Audit_Report.pdf" in res.headers["content-disposition"]
    # PDF starts with %PDF magic byte header
    assert res.content.startswith(b"%PDF")
    assert len(res.content) > 1000

def test_export_anomalies_excel():
    """Validates generation of ML Ghost Student Anomaly Excel sheet."""
    res = client.get("/api/v1/export/anomalies?format=excel")
    assert res.status_code == 200
    assert "application/vnd.openxmlformats" in res.headers["content-type"]
    assert len(res.content) > 2000

def test_export_students_csv_dpdp_masked():
    """Validates DPDP-compliant student roster export with masked APAAR numbers."""
    res = client.get("/api/v1/export/students?format=csv&mask_apaar=true")
    assert res.status_code == 200
    assert "text/csv" in res.headers["content-type"]
    lines = res.text.strip().split("\n")
    assert len(lines) > 5
    header = lines[0]
    assert "APAAR ID" in header
    assert "Document Hash" in header
    # Check that APAAR IDs are masked with XXXX-XXXX-
    first_data_row = lines[1]
    assert "XXXX-XXXX-" in first_data_row
