from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

class ProgramBranchResponse(BaseModel):
    id: str
    program: str
    branch: str
    academic_year: str
    approved_intake: int
    enrolled_count: int
    supernumerary_intake: int

    class Config:
        from_attributes = True

class InstitutionResponse(BaseModel):
    id: str
    aicte_id: str
    name: str
    code: str
    state: str
    region: str
    type: str
    trust_score: float
    approved_intake: int
    actual_enrolment: int
    supernumerary_intake: int
    status: str
    contact_email: Optional[str] = None
    phone: Optional[str] = None
    utilization_rate: Optional[float] = None

    class Config:
        from_attributes = True

class InstitutionDetailResponse(InstitutionResponse):
    programs: List[ProgramBranchResponse] = []
    created_at: datetime
    updated_at: datetime

class TrustScoreBreakdown(BaseModel):
    institution_id: str
    institution_name: str
    trust_score: float
    data_quality_factor: float
    timeliness_factor: float
    anomaly_penalty: float
    resolution_speed_factor: float
    audit_priority_rank: int
    trend: str
