from typing import Optional
from datetime import date, datetime
from pydantic import BaseModel

class StudentBase(BaseModel):
    apaar_id: str
    name: str
    dob: date
    gender: str
    program: str
    branch: str
    year_of_study: int
    admission_date: date
    quota_type: str = "Merit"
    category: str = "General"
    is_supernumerary: bool = False
    is_nri: bool = False
    is_oci: bool = False
    is_foreign_national: bool = False

class StudentCreate(StudentBase):
    institution_id: str
    program_branch_id: Optional[str] = None

class StudentResponse(BaseModel):
    id: str
    apaar_id: str
    institution_id: str
    institution_name: Optional[str] = None
    name: str
    dob: Optional[date] = None
    gender: str
    program: str
    branch: str
    year_of_study: int
    admission_date: date
    quota_type: str
    category: str
    is_supernumerary: bool
    is_nri: bool
    is_oci: bool
    is_foreign_national: bool
    verification_status: str
    document_hash: str
    created_at: datetime

    class Config:
        from_attributes = True

class StudentPublicClaim(BaseModel):
    """Selective disclosure claim for employers/regulators - masked PII"""
    apaar_id_masked: str
    program: str
    branch: str
    year_of_study: int
    institution_name: str
    institution_aicte_id: str
    aicte_approved: bool = True
    enrollment_valid: bool = True
    signed_by: str = "AICTE Central Authority"
    signature_ed25519: str
    timestamp: datetime
