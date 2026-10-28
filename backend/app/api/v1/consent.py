import random
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.student import Student
from app.models.consent import ConsentWallet, VerificationAccessLog
from app.schemas.verification import (
    ConsentPolicyItem,
    ConsentUpdateRequest,
    ConsentWalletResponse,
    VerificationAccessLogResponse
)
from app.services.audit_service import AuditService

router = APIRouter(prefix="/consent", tags=["DPDP Consent Wallet"])

DEFAULT_VERIFIER_TYPES = [
    {
        "verifier_type": "EMPLOYER",
        "allowed_fields": ["apaar_id_masked", "student_name", "institution_name", "program", "branch", "year_of_study", "aicte_approved", "verification_status"],
        "is_active": True
    },
    {
        "verifier_type": "UNIVERSITY",
        "allowed_fields": ["apaar_id_masked", "student_name", "institution_name", "program", "branch", "year_of_study", "admission_date", "aicte_approved", "verification_status"],
        "is_active": True
    },
    {
        "verifier_type": "PUBLIC_VERIFIER",
        "allowed_fields": ["apaar_id_masked", "student_name", "institution_name", "program", "branch", "aicte_approved"],
        "is_active": True
    }
]

@router.get("/wallet/{apaar_id}", response_model=ConsentWalletResponse)
def get_student_consent_wallet(
    apaar_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieves the DPDP Consent Wallet settings for a specific student APAAR ID.
    If first time viewing, seeds default privacy-preserving consent policies.
    """
    clean_apaar = apaar_id.replace("-", "").strip()
    student = db.query(Student).filter(Student.apaar_id == clean_apaar).first()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student APAAR not found")

    wallets = db.query(ConsentWallet).filter(ConsentWallet.student_apaar_id == clean_apaar).all()

    existing_types = {w.verifier_type for w in wallets}
    added_any = False
    for def_policy in DEFAULT_VERIFIER_TYPES:
        if def_policy["verifier_type"] not in existing_types:
            w = ConsentWallet(
                student_apaar_id=clean_apaar,
                verifier_type=def_policy["verifier_type"],
                allowed_fields=def_policy["allowed_fields"],
                is_active=def_policy["is_active"],
                otp_code="123456"
            )
            db.add(w)
            wallets.append(w)
            added_any = True
    if added_any:
        db.commit()


    policy_items = [
        ConsentPolicyItem(
            verifier_type=w.verifier_type,
            allowed_fields=w.allowed_fields or [],
            is_active=w.is_active,
            expires_at=w.expires_at
        ) for w in wallets
    ]

    # Active OTP for simulated demo authorization
    active_otp = wallets[0].otp_code if wallets and wallets[0].otp_code else "123456"

    return ConsentWalletResponse(
        student_apaar_id=clean_apaar,
        student_name=student.get_decrypted_name(),
        policies=policy_items,
        active_otp=active_otp
    )

@router.post("/wallet/update")
def update_student_consent_wallet(
    request_data: ConsentUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    Allows student to grant, narrow, or revoke field-level data access
    per verifier type (e.g. Employer can see Degree + College, but not Category or DOB).
    """
    clean_apaar = request_data.student_apaar_id.replace("-", "").strip()
    student = db.query(Student).filter(Student.apaar_id == clean_apaar).first()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student APAAR not found")

    for policy in request_data.policies:
        wallet = db.query(ConsentWallet).filter(
            ConsentWallet.student_apaar_id == clean_apaar,
            ConsentWallet.verifier_type == policy.verifier_type
        ).first()

        if wallet:
            wallet.allowed_fields = policy.allowed_fields
            wallet.is_active = policy.is_active
            wallet.expires_at = policy.expires_at
            wallet.updated_at = datetime.now(timezone.utc)
        else:
            wallet = ConsentWallet(
                student_apaar_id=clean_apaar,
                verifier_type=policy.verifier_type,
                allowed_fields=policy.allowed_fields,
                is_active=policy.is_active,
                expires_at=policy.expires_at,
                otp_code="123456"
            )
            db.add(wallet)

    db.commit()

    # Immutable Audit Log
    AuditService.append_log(
        db=db,
        action="CONSENT_POLICY_UPDATED",
        entity_type="CONSENT_WALLET",
        entity_id=clean_apaar,
        role="STUDENT",
        user_email=f"student.{clean_apaar[-4:]}@digilocker.gov.in",
        details={
            "policies_count": len(request_data.policies),
            "updated_types": [p.verifier_type for p in request_data.policies]
        }
    )

    return {
        "success": True,
        "message": "Consent policies successfully updated in student wallet.",
        "student_apaar_id": clean_apaar
    }

@router.post("/request-otp/{apaar_id}")
def generate_consent_otp(
    apaar_id: str,
    db: Session = Depends(get_db)
):
    """
    Simulates sending an OTP to the student's registered mobile number / DigiLocker
    for elevated verifier disclosure approval.
    """
    clean_apaar = apaar_id.replace("-", "").strip()
    student = db.query(Student).filter(Student.apaar_id == clean_apaar).first()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student APAAR not found")

    otp = str(random.randint(100000, 999999))
    # Update across student's wallets
    wallets = db.query(ConsentWallet).filter(ConsentWallet.student_apaar_id == clean_apaar).all()
    for w in wallets:
        w.otp_code = otp
    db.commit()

    return {
        "success": True,
        "otp": otp,
        "message": f"Simulated OTP [{otp}] dispatched to student's mobile number linked with APAAR ID {clean_apaar}."
    }

@router.get("/access-logs/{apaar_id}", response_model=List[VerificationAccessLogResponse])
def get_student_access_history(
    apaar_id: str,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    DPDP Act 2023 Right to Access & Transparency:
    Student views complete log of who accessed their record, purpose, organization, and fields accessed.
    """
    clean_apaar = apaar_id.replace("-", "").strip()
    logs = db.query(VerificationAccessLog).filter(
        VerificationAccessLog.student_apaar_id == clean_apaar
    ).order_by(VerificationAccessLog.timestamp.desc()).limit(limit).all()

    return logs
