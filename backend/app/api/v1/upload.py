import csv
import io
import json
import hashlib
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.rbac import UserRole, get_current_user, require_roles
from app.models.institution import Institution, ProgramBranch
from app.models.student import Student
from app.models.batch import UploadBatch, ValidationFlag
from app.services.column_mapper import ColumnMapper, CANONICAL_SCHEMA
from app.services.validation.engine import ValidationEngine
from app.services.apaar_service import ApaarService
from app.core.security import encrypt_pii

router = APIRouter(prefix="/upload", tags=["Upload Pipeline & Smart Assistant"])

@router.post("/preview")
async def preview_upload_file(
    file: UploadFile = File(...),
    user = Depends(get_current_user)
):
    """
    Smart Upload Assistant (Feature K):
    Inspects messy column headers from uploaded CSV/Excel, performs fuzzy mapping to canonical schema,
    and returns confidence scores + first 5 rows preview before final submission.
    """
    content = await file.read()
    filename = file.filename or "upload.csv"

    # Decode CSV
    try:
        text_stream = io.StringIO(content.decode("utf-8", errors="replace"))
        reader = csv.DictReader(text_stream)
        headers = reader.fieldnames or []
        sample_rows = []
        for i, row in enumerate(reader):
            if i >= 5:
                break
            sample_rows.append(row)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unable to parse upload file as CSV: {str(e)}"
        )

    mapping_analysis = ColumnMapper.auto_map_headers(list(headers))

    return {
        "filename": filename,
        "detected_headers": list(headers),
        "mapping_analysis": mapping_analysis,
        "sample_rows_preview": sample_rows,
        "total_preview_count": len(sample_rows)
    }

@router.post("/batch")
async def upload_student_batch(
    file: UploadFile = File(...),
    institution_id: Optional[str] = Form(None),
    column_mapping_json: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """
    Bulk Student Upload Endpoint:
    Parses CSV, maps columns, executes modular ValidationEngine, opens real-time clash cases,
    and outputs full batch statistics with row-by-row error grid.
    """
    target_inst_id = institution_id
    if user.role == UserRole.INSTITUTION_ADMIN.value:
        target_inst_id = str(user.institution_id)
    
    if not target_inst_id:
        # Fallback to first active institution if not provided
        first_inst = db.query(Institution).first()
        target_inst_id = str(first_inst.id) if first_inst else None

    if not target_inst_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Target institution_id required")

    inst = db.query(Institution).filter(Institution.id == target_inst_id).first()
    if not inst:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Institution not found")

    content = await file.read()
    file_hash = hashlib.sha256(content).hexdigest()
    filename = file.filename or "student_batch.csv"

    # Parse CSV
    try:
        text_stream = io.StringIO(content.decode("utf-8", errors="replace"))
        reader = csv.DictReader(text_stream)
        headers = reader.fieldnames or []
        raw_rows = list(reader)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to parse CSV: {str(e)}")

    # Resolve Column Mapping
    if column_mapping_json:
        try:
            mapping = json.loads(column_mapping_json)
        except Exception:
            mapping = ColumnMapper.auto_map_headers(list(headers))["mapping"]
    else:
        mapping = ColumnMapper.auto_map_headers(list(headers))["mapping"]

    # Transform rows to canonical schema
    canonical_records = [
        ColumnMapper.transform_row(row, mapping)
        for row in raw_rows
    ]

    # Create UploadBatch record
    batch = UploadBatch(
        institution_id=target_inst_id,
        filename=filename,
        file_hash=file_hash,
        total_records=len(canonical_records),
        processed_records=0,
        valid_records=0,
        flagged_records=0,
        status="PROCESSING",
        uploaded_by_user_id=str(user.id) if hasattr(user, "id") else None
    )
    db.add(batch)
    db.commit()
    db.refresh(batch)

    # Execute ValidationEngine
    engine = ValidationEngine()
    result = engine.process_batch(
        db=db,
        batch=batch,
        raw_records=canonical_records,
        user_email=user.email if hasattr(user, "email") else "admin@institution.edu"
    )

    return {
        "success": True,
        "batch_id": str(batch.id),
        "institution_name": inst.name,
        "filename": filename,
        "total_records": len(canonical_records),
        "valid_records": result["valid_records"],
        "flagged_records": result["flagged_records"],
        "issues_count": len(result["issues"]),
        "error_grid": result["issues"]
    }

@router.post("/single-entry")
def submit_single_student_entry(
    payload: Dict[str, Any],
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """Single student manual admission entry with immediate inline validation and seat lock checks."""
    target_inst_id = str(user.institution_id) if user.role == UserRole.INSTITUTION_ADMIN.value else payload.get("institution_id")
    if not target_inst_id:
        inst = db.query(Institution).first()
        target_inst_id = str(inst.id) if inst else None

    engine = ValidationEngine()
    context = engine.build_context(db, target_inst_id)
    issues = engine.validate_record(payload, context)

    critical_or_high = [i for i in issues if i.severity in [RuleSeverity.CRITICAL, RuleSeverity.HIGH]]
    if critical_or_high:
        return {
            "success": False,
            "blocked": True,
            "message": "Student registration blocked by AICTE validation rules.",
            "violations": [
                {"rule_code": i.rule_code, "severity": i.severity.value, "message": i.message, "fix_suggestion": i.fix_suggestion}
                for i in issues
            ]
        }

    # If valid, insert student into database
    apaar_id = str(payload.get("apaar_id", "")).strip().replace(" ", "").replace("-", "")
    full_name = str(payload.get("name", "Unknown Student"))
    
    from datetime import date
    dob_val = date.fromisoformat(payload["dob"]) if "dob" in payload else date(2004, 1, 1)
    adm_val = date.fromisoformat(payload["admission_date"]) if "admission_date" in payload else date(2025, 7, 1)

    doc_hash = hashlib.sha256(f"{apaar_id}_{full_name}".encode()).hexdigest()

    student = Student(
        apaar_id=apaar_id,
        institution_id=target_inst_id,
        name_encrypted=encrypt_pii(full_name),
        dob_encrypted=encrypt_pii(dob_val.isoformat()),
        cached_name=full_name,
        cached_dob=dob_val,
        gender=payload.get("gender", "Male"),
        program=payload.get("program", "UG"),
        branch=payload.get("branch", "Computer Science & Engineering"),
        year_of_study=int(payload.get("year_of_study", 1)),
        admission_date=adm_val,
        quota_type=payload.get("quota_type", "Merit"),
        category=payload.get("category", "General"),
        is_supernumerary=bool(payload.get("is_supernumerary", False)),
        is_nri=bool(payload.get("is_nri", False)),
        is_oci=bool(payload.get("is_oci", False)),
        is_foreign_national=bool(payload.get("is_foreign_national", False)),
        document_hash=doc_hash,
        verification_status="VALIDATED"
    )
    db.add(student)
    
    # Increment institution count
    inst = db.query(Institution).filter(Institution.id == target_inst_id).first()
    if inst:
        inst.actual_enrolment += 1
    db.commit()

    return {
        "success": True,
        "blocked": False,
        "message": f"Student {full_name} (APAAR: {apaar_id}) successfully enrolled and verified.",
        "student_id": str(student.id),
        "apaar_id": apaar_id
    }

@router.get("/batches")
def list_upload_batches(
    institution_id: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    query = db.query(UploadBatch)
    if user.role == UserRole.INSTITUTION_ADMIN.value and user.institution_id:
        query = query.filter(UploadBatch.institution_id == user.institution_id)
    elif institution_id:
        query = query.filter(UploadBatch.institution_id == institution_id)

    batches = query.order_by(UploadBatch.created_at.desc()).limit(limit).all()
    return batches

@router.get("/batches/{batch_id}/flags")
def get_batch_flags(
    batch_id: str,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """Returns row-by-row error grid with fix suggestions for a given batch."""
    flags = db.query(ValidationFlag).filter(ValidationFlag.upload_batch_id == batch_id).all()
    return flags

@router.post("/flags/{flag_id}/resolve")
def resolve_flag(
    flag_id: str,
    action: str = Query("AUTO_FIX", description="AUTO_FIX or MANUAL_OVERRIDE"),
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """Resolves an error grid flag with resolution notes."""
    flag = db.query(ValidationFlag).filter(ValidationFlag.id == flag_id).first()
    if not flag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flag not found")

    flag.resolved = True
    flag.resolved_by = f"{user.role}:{action}"
    flag.resolved_at = datetime.now(timezone.utc)
    db.commit()
    return {"success": True, "flag_id": flag_id, "resolved": True}

@router.get("/sample-csv")
def download_demo_sample_csv():
    """
    Generates a realistic 500-row demo CSV with messy column headers
    and planted anomalies matching Demo Script step 1 & 2.
    """
    output = io.StringIO()
    # Intentionally messy headers for Smart Assistant demonstration
    headers = [
        "APAAR_NO", "Candidate Name", "Date_of_Birth", "Sex", "Degree_Level",
        "Discipline_Branch", "Study_Year", "Admission_Date", "Quota_Category",
        "Social_Category", "Supernumerary_Seat", "NRI_Quota"
    ]
    writer = csv.writer(output)
    writer.writerow(headers)

    counter = 50000000000
    for i in range(1, 480):
        counter += 1
        apaar = ApaarService.generate_valid_apaar(str(counter)[:11])
        writer.writerow([
            apaar, f"Demo Candidate {i}", "2004-05-12", "Male" if i % 2 == 0 else "Female",
            "UG", "Computer Science & Engineering", 1, "2025-07-15", "Merit", "General", "No", "No"
        ])

    # Planted 6 Duplicates
    dup_apaar = ApaarService.generate_valid_apaar("50000099991")
    for _ in range(6):
        writer.writerow([
            dup_apaar, "Duplicate Candidate Demo", "2004-01-10", "Female",
            "UG", "Computer Science & Engineering", 1, "2025-07-18", "Merit", "OBC", "No", "No"
        ])

    # Planted 4 Invalid APAAR IDs
    writer.writerow(["1234567890", "Bad Length Short", "2004-02-10", "Male", "UG", "Mechanical Engineering", 1, "2025-07-20", "Merit", "General", "No", "No"])
    writer.writerow(["99887766554433", "Bad Length Long", "2004-03-11", "Female", "UG", "Mechanical Engineering", 1, "2025-07-20", "Merit", "General", "No", "No"])
    writer.writerow(["112233445567", "Bad Checksum One", "2004-04-12", "Male", "UG", "Mechanical Engineering", 1, "2025-07-20", "Merit", "General", "No", "No"])
    writer.writerow(["998877665541", "Bad Checksum Two", "2004-05-13", "Female", "UG", "Mechanical Engineering", 1, "2025-07-20", "Merit", "General", "No", "No"])

    # Planted 2 Cross-College Clashes (Active at IIT Delhi & CEG Chennai)
    writer.writerow(["992817263541", "Rohan Verma", "2004-05-14", "Male", "UG", "Computer Science & Engineering", 1, "2025-08-01", "Management", "General", "No", "No"])
    writer.writerow(["883719204852", "Pooja Sundaram", "2003-11-20", "Female", "UG", "Electronics & Communication Engineering", 1, "2025-08-01", "Merit", "OBC", "No", "No"])

    csv_data = output.getvalue()
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=demo_sample_student_batch.csv"}
    )
