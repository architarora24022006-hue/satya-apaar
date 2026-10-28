from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class VerificationRequest(BaseModel):
    apaar_id: str = Field(..., description="12-digit APAAR ID of the student")
    verifier_name: str = Field(..., description="Name of the person or agent conducting verification")
    verifier_org: str = Field(..., description="Organization/Company requesting verification")
    verifier_role: str = Field("EMPLOYER_VERIFIER", description="Role: EMPLOYER_VERIFIER, UNIVERSITY_REGULATOR, or PUBLIC_VERIFIER")
    purpose: str = Field("Employment Background Check", description="Purpose for accessing student credentials")
    otp_code: Optional[str] = Field(None, description="6-digit simulated OTP for student-approved elevated disclosure")

class VerificationResponse(BaseModel):
    apaar_id: str
    apaar_id_masked: str
    student_name: str
    verification_status: str
    institution_name: str
    institution_aicte_id: str
    program: str
    branch: str
    year_of_study: int
    aicte_approved: bool
    disclosed_data: Dict[str, Any]
    restricted_fields: List[str]
    consent_status: str
    canonical_claim: Dict[str, Any]
    signature_ed25519: str
    public_key_b64: str
    qr_payload: str
    verified_at: datetime
    access_log_id: str

class OfflineVerificationRequest(BaseModel):
    claim: Dict[str, Any]
    signature_ed25519: str
    public_key_b64: Optional[str] = None

class OfflineVerificationResponse(BaseModel):
    is_valid: bool
    algorithm: str = "Ed25519"
    issuer: str
    verified_at: datetime
    message: str
    claim: Optional[Dict[str, Any]] = None

class ConsentPolicyItem(BaseModel):
    verifier_type: str
    allowed_fields: List[str]
    is_active: bool = True
    expires_at: Optional[datetime] = None

class ConsentUpdateRequest(BaseModel):
    student_apaar_id: str
    policies: List[ConsentPolicyItem]

class ConsentWalletResponse(BaseModel):
    student_apaar_id: str
    student_name: str
    policies: List[ConsentPolicyItem]
    active_otp: Optional[str] = None

class VerificationAccessLogResponse(BaseModel):
    id: str
    student_apaar_id: str
    verifier_name: str
    verifier_org: str
    verifier_role: str
    purpose: str
    accessed_fields: List[str]
    ip_address: str
    timestamp: datetime

    class Config:
        from_attributes = True
