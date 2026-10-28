from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.database import get_db
from app.core.rbac import UserRole, get_current_user, require_roles
from app.models.audit import AuditLog
from app.schemas.audit import AuditLogResponse, AuditIntegrityCheckResult
from app.services.audit_service import AuditService

router = APIRouter(prefix="/audit", tags=["Cryptographic Audit Trail"])

@router.get("/logs", response_model=List[AuditLogResponse])
def get_audit_logs(
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """Retrieves immutable, hash-chained audit logs."""
    query = db.query(AuditLog)
    if action:
        query = query.filter(AuditLog.action == action)
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)

    logs = query.order_by(desc(AuditLog.sequence_number)).offset(offset).limit(limit).all()
    return logs

@router.get("/verify-integrity", response_model=AuditIntegrityCheckResult)
def verify_audit_trail_integrity(db: Session = Depends(get_db)):
    """
    Validates complete SHA-256 hash chain from Genesis block (#1) to current tip.
    Returns whether the ledger has remained completely untampered or where breakage occurred.
    """
    result = AuditService.verify_chain_integrity(db)
    return AuditIntegrityCheckResult(**result)

@router.post("/tamper-demo")
def tamper_record_demo(
    sequence_number: int = Query(3, description="Sequence number of the record to tamper with for demonstration"),
    db: Session = Depends(get_db)
):
    """
    [DEMO EXCLUSIVE] Injects a malicious payload alteration into a historical block
    to demonstrate real-time cryptographic tamper detection in front of hackathon judges.
    """
    success = AuditService.tamper_entry_for_demo(db, sequence_number)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit record #{sequence_number} not found"
        )
    return {
        "tampered": True,
        "sequence_number": sequence_number,
        "message": f"Block #{sequence_number} payload has been altered. Click 'Verify Chain Integrity' to see the alert!"
    }

@router.post("/restore-demo")
def restore_record_demo(
    sequence_number: int = Query(3, description="Sequence number of the record to restore"),
    db: Session = Depends(get_db)
):
    """
    [DEMO EXCLUSIVE] Heals the tampered historical block back to its authentic state,
    returning the entire chain back to 100% cryptographic integrity.
    """
    success = AuditService.restore_entry_for_demo(db, sequence_number)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit record #{sequence_number} not found"
        )
    return {
        "restored": True,
        "sequence_number": sequence_number,
        "message": f"Block #{sequence_number} integrity restored. Click 'Verify Chain Integrity' to confirm green check!"
    }

