import os
import sys
import io
import csv
import json
import pytest
from datetime import date, timedelta
from fastapi.testclient import TestClient

# Add backend directory to sys.path
sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), '..')))

from app.main import app
from app.core.database import SessionLocal
from app.models.institution import Institution
from app.models.student import Student
from app.models.case import Case
from app.models.batch import UploadBatch, ValidationFlag
from app.services.apaar_service import ApaarService
from app.services.validation.base_rule import RuleSeverity
from app.services.validation.engine import ValidationEngine
from app.services.validation.rules.apaar_format_rule import ApaarFormatRule
from app.services.validation.rules.duplicate_within_institution_rule import DuplicateWithinInstitutionRule
from app.services.validation.rules.cross_institution_clash_rule import CrossInstitutionClashRule
from app.services.validation.rules.intake_capacity_rule import IntakeCapacityRule
from app.services.validation.rules.logical_consistency_rules import LogicalConsistencyRule

client = TestClient(app)

@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_apaar_format_and_checksum_rule(db_session):
    rule = ApaarFormatRule()
    inst = db_session.query(Institution).first()
    engine = ValidationEngine()
    context = engine.build_context(db_session, str(inst.id))

    # Valid APAAR
    valid_id = ApaarService.generate_valid_apaar("10000000001")
    issues = rule.validate({"apaar_id": valid_id}, context)
    assert len(issues) == 0

    # Short APAAR (10 digits)
    issues_short = rule.validate({"apaar_id": "1234567890"}, context)
    assert any(i.rule_code == "APAAR_INVALID_LENGTH" for i in issues_short)

    # Corrupt Checksum
    corrupt_id = valid_id[:-1] + ("0" if valid_id[-1] != "0" else "1")
    issues_corrupt = rule.validate({"apaar_id": corrupt_id}, context)
    assert any(i.rule_code == "APAAR_CHECKSUM_FAILED" for i in issues_corrupt)

    # Auto-clean spaces/hyphens
    spaced_id = f"{valid_id[:4]}-{valid_id[4:8]}-{valid_id[8:]}"
    issues_clean = rule.validate({"apaar_id": spaced_id}, context)
    assert any(i.auto_fixable and i.fixed_value == valid_id for i in issues_clean)

def test_duplicate_within_institution_rule(db_session):
    rule = DuplicateWithinInstitutionRule()
    inst = db_session.query(Institution).first()
    engine = ValidationEngine()
    context = engine.build_context(db_session, str(inst.id))

    test_apaar = ApaarService.generate_valid_apaar("20000000001")
    # First appearance
    issues_1 = rule.validate({"apaar_id": test_apaar}, context)
    assert len(issues_1) == 0

    # Duplicate in same batch
    issues_2 = rule.validate({"apaar_id": test_apaar}, context)
    assert any(i.rule_code == "BATCH_DUPLICATE_APAAR" for i in issues_2)

def test_cross_institution_clash_rule(db_session):
    rule = CrossInstitutionClashRule()
    # Student Rohan Verma is seeded at IIT Delhi (clash_apaar_1: 992817263541)
    clash_apaar = "992817263541"
    
    # Try uploading this APAAR to a different institution
    other_inst = db_session.query(Institution).filter(Institution.code == "COEP").first()
    engine = ValidationEngine()
    context = engine.build_context(db_session, str(other_inst.id))

    issues = rule.validate({"apaar_id": clash_apaar}, context)
    assert len(issues) > 0
    assert issues[0].rule_code == "CROSS_INSTITUTION_DUPLICATE"
    assert issues[0].severity == RuleSeverity.CRITICAL

def test_intake_capacity_and_seat_lock(db_session):
    rule = IntakeCapacityRule()
    inst = db_session.query(Institution).first()
    engine = ValidationEngine()
    context = engine.build_context(db_session, str(inst.id))

    # Mock capacity scenario: approved=10, current=9 (90% capacity)
    context.branch_intake_map["Test Branch"] = {"approved": 10, "current": 9}
    issues_warn = rule.validate({"branch": "Test Branch", "is_supernumerary": False}, context)
    assert any(i.rule_code == "SEAT_WARNING_90_PERCENT" for i in issues_warn)

    # 100% capacity reached (approved=10, current=10)
    context.branch_intake_map["Test Branch"] = {"approved": 10, "current": 10}
    issues_lock = rule.validate({"branch": "Test Branch", "is_supernumerary": False}, context)
    assert any(i.rule_code == "SEAT_LOCK_BREACH" for i in issues_lock)

    # Supernumerary seat bypasses regular lock
    issues_sn = rule.validate({"branch": "Test Branch", "is_supernumerary": True}, context)
    assert not any(i.rule_code == "SEAT_LOCK_BREACH" for i in issues_sn)

def test_logical_consistency_rules(db_session):
    rule = LogicalConsistencyRule()
    inst = db_session.query(Institution).first()
    engine = ValidationEngine()
    context = engine.build_context(db_session, str(inst.id))

    # Underage student (born in 2018 entering college in 2025 -> 7 years old)
    issues_underage = rule.validate({
        "dob": "2018-01-01",
        "admission_date": "2025-07-15"
    }, context)
    assert any(i.rule_code == "IMPOSSIBLE_AGE_UNDERAGE" for i in issues_underage)

    # Conflict NRI and Foreign National
    issues_conflict = rule.validate({
        "is_nri": True,
        "is_foreign_national": True
    }, context)
    assert any(i.rule_code == "CONFLICT_NRI_FOREIGN_NATIONAL" for i in issues_conflict)

    # Supernumerary without justification
    issues_sn = rule.validate({
        "is_supernumerary": True,
        "quota_type": "Merit"
    }, context)
    assert any(i.rule_code == "SUPERNUMERARY_WITHOUT_JUSTIFICATION" for i in issues_sn)

def test_upload_batch_integration_flow():
    # Login as Institution Admin (IIT Delhi)
    login_res = client.post("/api/v1/auth/login", json={
        "email": "admin@iitd.ac.in",
        "password": "Password@123"
    })
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Generate a test mini-CSV
    csv_content = (
        "APAAR_NO,Candidate Name,Date_of_Birth,Sex,Degree_Level,Discipline_Branch,Study_Year,Admission_Date,Quota_Category,Social_Category\n"
        "100000000014,Test Valid Student,2004-05-10,Male,UG,Computer Science & Engineering,1,2025-07-15,Merit,General\n"
        "12345,Invalid Short APAAR,2004-05-10,Male,UG,Computer Science & Engineering,1,2025-07-15,Merit,General\n"
        "992817263541,Rohan Verma Clash,2004-05-14,Male,UG,Computer Science & Engineering,1,2025-07-15,Merit,General\n"
    )

    # 1. Preview endpoint
    preview_res = client.post(
        "/api/v1/upload/preview",
        headers=headers,
        files={"file": ("test.csv", csv_content.encode("utf-8"), "text/csv")}
    )
    assert preview_res.status_code == 200
    preview_data = preview_res.json()
    assert "mapping_analysis" in preview_data
    assert "APAAR_NO" in preview_data["mapping_analysis"]["mapping"]

    # 2. Upload Batch endpoint
    batch_res = client.post(
        "/api/v1/upload/batch",
        headers=headers,
        files={"file": ("test.csv", csv_content.encode("utf-8"), "text/csv")},
        data={"column_mapping_json": json.dumps(preview_data["mapping_analysis"]["mapping"])}
    )
    assert batch_res.status_code == 200
    batch_data = batch_res.json()
    assert batch_data["total_records"] == 3
    assert batch_data["flagged_records"] >= 2
    assert any(i["rule_code"] == "APAAR_INVALID_LENGTH" for i in batch_data["error_grid"])

    # 3. Check case management list
    case_res = client.get("/api/v1/cases/", headers=headers)
    assert case_res.status_code == 200
    cases_list = case_res.json()
    assert len(cases_list) > 0
