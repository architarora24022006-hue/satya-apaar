from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.rbac import UserRole, get_current_user, require_roles
from app.models.case import Case
from app.models.batch import UploadBatch
from app.models.institution import ProgramBranch

from app.services.agent.sentinel_agent import SentinelAgent
from app.services.audit_service import AuditService

router = APIRouter(prefix="/sentinel", tags=["Sentinel AI Agent"])

class TriageRequest(BaseModel):
    batch_id: Optional[str] = None

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[Dict[str, str]]] = None

class ApprovalDecisionRequest(BaseModel):
    case_id: str
    decision: str  # APPROVE or REJECT
    officer_notes: Optional[str] = None

@router.post("/triage-batch")
def run_autonomous_batch_triage(
    payload: TriageRequest,
    db: Session = Depends(get_db)
):
    """
    Triggers the Sentinel AI Agent autonomous triage pipeline.
    Steps: Ingest & Plan -> Validation & Investigation -> Risk Assessment -> Action Execution / Human Approval.
    """
    target_batch_id = payload.batch_id
    if not target_batch_id:
        latest = db.query(UploadBatch).order_by(UploadBatch.created_at.desc()).first()
        if not latest:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No upload batches available to triage."
            )
        target_batch_id = str(latest.id)

    result = SentinelAgent.triage_batch(db, target_batch_id)
    return result

@router.post("/chat")
def chat_with_sentinel(
    payload: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    Conversational AI Assistant ('Ask Sentinel').
    Answers questions about anomalies, colleges, seat saturation, and compliance rules using tool use.
    """
    result = SentinelAgent.chat_with_sentinel(db, payload.message, payload.history)
    return result

@router.get("/batches")
def get_triagable_batches(
    limit: int = Query(15, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Returns recent upload batches with institution context for Sentinel triage selection."""
    from app.models.institution import Institution
    batches = db.query(UploadBatch).order_by(UploadBatch.created_at.desc()).limit(limit).all()
    results = []
    for b in batches:
        inst = db.query(Institution).filter(Institution.id == b.institution_id).first()
        results.append({
            "id": str(b.id),
            "filename": b.filename,
            "institution_id": str(b.institution_id),
            "institution_name": inst.name if inst else "Institution",
            "state": inst.state if inst else "Unknown",
            "total_records": b.total_records,
            "valid_records": b.valid_records,
            "flagged_records": b.flagged_records,
            "status": b.status,
            "created_at": b.created_at.isoformat() if b.created_at else None
        })
    return results

@router.get("/pending-approvals")
def get_pending_human_approvals(
    db: Session = Depends(get_db)
):
    """Retrieves all high-stakes sanctions waiting for AICTE Regional Officer human sign-off."""
    pending = db.query(Case).filter(Case.status == "PENDING_APPROVAL").order_by(Case.created_at.desc()).all()
    
    results = []
    for c in pending:
        results.append({
            "case_id": str(c.id),
            "case_number": c.case_number,
            "title": c.title,
            "institution_id": str(c.institution_id),
            "priority": c.priority,
            "status": c.status,
            "description": c.description,
            "proposed_action": c.action_draft or "Sanction Pending Review",
            "evidence_pack": c.evidence_pack,
            "created_at": c.created_at.isoformat(),
            "sla_deadline": c.sla_deadline.isoformat() if c.sla_deadline else None
        })
    return results

@router.post("/decide-approval")
def decide_human_approval(
    payload: ApprovalDecisionRequest,
    db: Session = Depends(get_db)
):
    """
    Human-in-the-Loop decision endpoint: AICTE Regional Officer Approves or Rejects Sentinel's proposed sanction.
    """
    case = db.query(Case).filter(Case.id == payload.case_id).first()
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Approval Case {payload.case_id} not found."
        )

    decision_upper = payload.decision.upper()
    now = datetime.now(timezone.utc)

    if decision_upper == "APPROVE":
        case.status = "RESOLVED"
        case.resolution_notes = f"APPROVED BY HUMAN OFFICER: {payload.officer_notes or 'Sanction confirmed by Regional Authority'}"
        
        # If the case was FREEZE_SEATS, lock the institution's branches
        if case.evidence_pack and case.evidence_pack.get("action_type") == "FREEZE_SEATS":
            branches = db.query(ProgramBranch).filter(ProgramBranch.institution_id == case.institution_id).all()
            for b in branches:
                b.is_locked = True
        
        action_name = "SENTINEL_SANCTION_APPROVED"
        msg = f"Sanction '{case.title}' approved by Human Officer. Action executed."
    else:
        case.status = "REJECTED"
        case.resolution_notes = f"REJECTED BY HUMAN OFFICER: {payload.officer_notes or 'Dismissed by Regional Authority'}"
        action_name = "SENTINEL_SANCTION_REJECTED"
        msg = f"Sanction '{case.title}' dismissed by Human Officer."

    case.updated_at = now
    db.commit()

    # Immutable Audit Log
    AuditService.append_log(
        db=db,
        action=action_name,
        entity_type="CASE",
        entity_id=str(case.id),
        role="REGIONAL_OFFICER",
        details={
            "case_number": case.case_number,
            "decision": decision_upper,
            "notes": payload.officer_notes
        }
    )

    return {
        "success": True,
        "case_id": str(case.id),
        "case_number": case.case_number,
        "decision": decision_upper,
        "message": msg
    }
