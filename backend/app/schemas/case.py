from typing import Any, Dict, Optional
from datetime import datetime
from pydantic import BaseModel

class CaseResponse(BaseModel):
    id: str
    case_number: str
    title: str
    institution_id: str
    institution_name: Optional[str] = None
    clash_institution_id: Optional[str] = None
    clash_institution_name: Optional[str] = None
    related_student_apaar: Optional[str] = None
    status: str
    priority: str
    sla_deadline: Optional[datetime] = None
    opened_by_type: str
    description: str
    action_draft: Optional[str] = None
    resolution_notes: Optional[str] = None
    evidence_pack: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class CaseUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    resolution_notes: Optional[str] = None
    action_draft: Optional[str] = None
