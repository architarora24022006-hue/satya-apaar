from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_public_key_b64
from app.schemas.verification import (
    VerificationRequest,
    VerificationResponse,
    OfflineVerificationRequest,
    OfflineVerificationResponse
)
from app.services.verification_service import VerificationService

router = APIRouter(prefix="/verification", tags=["Authorized Verification & Credentials"])

@router.post("/verify", response_model=VerificationResponse)
def verify_student(
    request_data: VerificationRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Authorized verification endpoint for Employers, Regulators, and Public Verifiers.
    Complies with DPDP Act 2023 with selective disclosure, consent enforcement,
    and Ed25519 verifiable credential generation.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"
    
    result = VerificationService.verify_student_record(
        db=db,
        apaar_id=request_data.apaar_id.replace("-", "").strip(),
        verifier_name=request_data.verifier_name,
        verifier_org=request_data.verifier_org,
        verifier_role=request_data.verifier_role,
        purpose=request_data.purpose,
        otp_code=request_data.otp_code,
        ip_address=client_ip
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with APAAR ID {request_data.apaar_id} not found in AICTE Central Repository"
        )

    return VerificationResponse(**result)

@router.post("/verify-offline", response_model=OfflineVerificationResponse)
def verify_offline_credential(
    payload: OfflineVerificationRequest
):
    """
    Standalone offline verification of Ed25519 signed QR credential.
    Requires ZERO database access or internet connectivity.
    Demonstrates tamper detection: if even a single character in the claim is changed,
    the signature validation will fail in red.
    """
    result = VerificationService.verify_offline_claim(
        claim=payload.claim,
        signature_ed25519=payload.signature_ed25519,
        public_key_b64=payload.public_key_b64
    )
    return OfflineVerificationResponse(**result)

@router.get("/public-key")
def get_root_public_key():
    """Returns AICTE Central Authority Ed25519 public root key for offline verifiers."""
    return {
        "public_key_b64": get_public_key_b64(),
        "algorithm": "Ed25519",
        "authority": "AICTE-SATYA-APAAR-CENTRAL",
        "key_usage": "Digital Student Credential Attestation"
    }
