from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.rbac import UserRole, get_current_user, require_roles
from app.core.security import sign_claim, get_public_key_b64
from app.models.student import Student
from app.models.institution import Institution
from app.schemas.student import StudentResponse, StudentPublicClaim
from app.services.audit_service import AuditService

router = APIRouter(prefix="/students", tags=["Students & Verification"])

@router.get("/", response_model=List[StudentResponse])
def list_students(
    institution_id: Optional[str] = None,
    program: Optional[str] = None,
    branch: Optional[str] = None,
    search: Optional[str] = None,
    verification_status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """Lists students filtered by RBAC and parameters."""
    query = db.query(Student)

    # Institution admin restricted to own students
    if user.role == UserRole.INSTITUTION_ADMIN.value and user.institution_id:
        query = query.filter(Student.institution_id == user.institution_id)
    elif institution_id:
        query = query.filter(Student.institution_id == institution_id)

    # Student restricted to own APAAR
    if user.role == UserRole.STUDENT.value:
        query = query.filter(Student.cached_name == user.full_name)

    if program:
        query = query.filter(Student.program.ilike(f"%{program}%"))
    if branch:
        query = query.filter(Student.branch.ilike(f"%{branch}%"))
    if verification_status:
        query = query.filter(Student.verification_status == verification_status.upper())
    if search:
        query = query.filter(
            (Student.apaar_id.ilike(f"%{search}%")) |
            (Student.cached_name.ilike(f"%{search}%"))
        )

    students = query.order_by(Student.created_at.desc()).offset(offset).limit(limit).all()

    results = []
    for s in students:
        inst_name = s.institution.name if s.institution else None
        results.append(StudentResponse(
            id=str(s.id),
            apaar_id=s.apaar_id,
            institution_id=str(s.institution_id),
            institution_name=inst_name,
            name=s.get_decrypted_name(),
            dob=s.get_decrypted_dob(),
            gender=s.gender,
            program=s.program,
            branch=s.branch,
            year_of_study=s.year_of_study,
            admission_date=s.admission_date,
            quota_type=s.quota_type,
            category=s.category,
            is_supernumerary=s.is_supernumerary,
            is_nri=s.is_nri,
            is_oci=s.is_oci,
            is_foreign_national=s.is_foreign_national,
            verification_status=s.verification_status,
            document_hash=s.document_hash,
            created_at=s.created_at
        ))
    return results

@router.get("/{apaar_id}", response_model=StudentResponse)
def get_student_by_apaar(
    apaar_id: str,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """Retrieves full student record with DPDP-aligned RBAC access logging."""
    student = db.query(Student).filter(Student.apaar_id == apaar_id).first()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found with specified APAAR ID")

    # RBAC check
    if user.role == UserRole.INSTITUTION_ADMIN.value and user.institution_id != str(student.institution_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to student enrolled at another college")

    # Audit log access
    AuditService.append_log(
        db=db,
        action="STUDENT_RECORD_ACCESSED",
        entity_type="STUDENT",
        entity_id=student.apaar_id,
        role=user.role,
        user_id=str(user.id),
        user_email=user.email,
        details={"apaar_id": student.apaar_id, "institution_id": str(student.institution_id)}
    )

    return StudentResponse(
        id=str(student.id),
        apaar_id=student.apaar_id,
        institution_id=str(student.institution_id),
        institution_name=student.institution.name if student.institution else None,
        name=student.get_decrypted_name(),
        dob=student.get_decrypted_dob(),
        gender=student.gender,
        program=student.program,
        branch=student.branch,
        year_of_study=student.year_of_study,
        admission_date=student.admission_date,
        quota_type=student.quota_type,
        category=student.category,
        is_supernumerary=student.is_supernumerary,
        is_nri=student.is_nri,
        is_oci=student.is_oci,
        is_foreign_national=student.is_foreign_national,
        verification_status=student.verification_status,
        document_hash=student.document_hash,
        created_at=student.created_at
    )

@router.get("/{apaar_id}/public-claim", response_model=StudentPublicClaim)
def get_verifiable_public_claim(
    apaar_id: str,
    db: Session = Depends(get_db)
):
    """
    Returns signed selective disclosure claim for offline verification by employers & regulators.
    Does NOT leak sensitive PII (DOB, category, or full Aadhaar/identity).
    Signed with AICTE Ed25519 private key.
    """
    student = db.query(Student).filter(Student.apaar_id == apaar_id).first()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student APAAR record not found")

    masked_apaar = f"XXXX-XXXX-{student.apaar_id[-4:]}"
    now = datetime.now(timezone.utc)
    
    claim_payload = {
        "apaar_id_masked": masked_apaar,
        "program": student.program,
        "branch": student.branch,
        "year_of_study": student.year_of_study,
        "institution_name": student.institution.name if student.institution else "AICTE Institute",
        "institution_aicte_id": student.institution.aicte_id if student.institution else "1-00000000",
        "aicte_approved": True,
        "enrollment_valid": student.verification_status in ["VALIDATED", "VERIFIED"],
        "timestamp": now.isoformat(),
        "issuer": "AICTE_CENTRAL_AUTHORITY"
    }

    signature = sign_claim(claim_payload)

    return StudentPublicClaim(
        apaar_id_masked=masked_apaar,
        program=student.program,
        branch=student.branch,
        year_of_study=student.year_of_study,
        institution_name=claim_payload["institution_name"],
        institution_aicte_id=claim_payload["institution_aicte_id"],
        aicte_approved=True,
        enrollment_valid=claim_payload["enrollment_valid"],
        signed_by="AICTE Central Authority (Ed25519)",
        signature_ed25519=signature,
        timestamp=now
    )
