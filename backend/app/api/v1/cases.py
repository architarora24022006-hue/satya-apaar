from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.database import get_db
from app.core.rbac import UserRole, get_current_user, require_roles
from app.models.case import Case
from app.models.institution import Institution
from app.schemas.case import CaseResponse, CaseUpdate
from app.services.audit_service import AuditService

router = APIRouter(prefix="/cases", tags=["Case Management & Dispute Resolution"])

@router.get("/", response_model=List[CaseResponse])
def list_cases(
    status_filter: Optional[str] = Query(None, alias="status"),
    priority: Optional[str] = None,
    institution_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """Lists dispute resolution cases with SLA deadlines and urgency prioritization."""
    query = db.query(Case)

    if user.role == UserRole.INSTITUTION_ADMIN.value and user.institution_id:
        query = query.filter(
            (Case.institution_id == user.institution_id) |
            (Case.clash_institution_id == user.institution_id)
        )
    elif institution_id:
        query = query.filter(Case.institution_id == institution_id)

    if status_filter:
        query = query.filter(Case.status == status_filter.upper())
    if priority:
        query = query.filter(Case.priority == priority.upper())

    cases = query.order_by(desc(Case.priority), Case.sla_deadline.asc()).offset(offset).limit(limit).all()

    results = []
    for c in cases:
        inst_a = db.query(Institution).filter(Institution.id == c.institution_id).first()
        inst_b = db.query(Institution).filter(Institution.id == c.clash_institution_id).first() if c.clash_institution_id else None

        results.append(CaseResponse(
            id=str(c.id),
            case_number=c.case_number,
            title=c.title,
            institution_id=str(c.institution_id),
            institution_name=inst_a.name if inst_a else None,
            clash_institution_id=str(c.clash_institution_id) if c.clash_institution_id else None,
            clash_institution_name=inst_b.name if inst_b else None,
            related_student_apaar=c.related_student_apaar,
            status=c.status,
            priority=c.priority,
            sla_deadline=c.sla_deadline,
            opened_by_type=c.opened_by_type,
            description=c.description,
            action_draft=c.action_draft,
            resolution_notes=c.resolution_notes,
            evidence_pack=c.evidence_pack,
            created_at=c.created_at,
            updated_at=c.updated_at
        ))
    return results

@router.get("/stats/summary")
def get_case_statistics(db: Session = Depends(get_db), user = Depends(get_current_user)):
    """Computes case management overview stats for dashboard banner."""
    total_open = db.query(Case).filter(Case.status.in_(["OPEN", "IN_REVIEW", "PENDING_APPROVAL"])).count()
    urgent_cases = db.query(Case).filter(
        Case.status.in_(["OPEN", "IN_REVIEW"]),
        Case.priority == "URGENT"
    ).count()
    resolved_count = db.query(Case).filter(Case.status == "RESOLVED").count()

    return {
        "active_cases_count": total_open,
        "urgent_clashes_count": urgent_cases,
        "resolved_cases_count": resolved_count,
        "average_resolution_hours": 18.5
    }

@router.get("/{id}", response_model=CaseResponse)
def get_case_detail(id: str, db: Session = Depends(get_db), user = Depends(get_current_user)):
    c = db.query(Case).filter(Case.id == id).first()
    if not c:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")

    inst_a = db.query(Institution).filter(Institution.id == c.institution_id).first()
    inst_b = db.query(Institution).filter(Institution.id == c.clash_institution_id).first() if c.clash_institution_id else None

    return CaseResponse(
        id=str(c.id),
        case_number=c.case_number,
        title=c.title,
        institution_id=str(c.institution_id),
        institution_name=inst_a.name if inst_a else None,
        clash_institution_id=str(c.clash_institution_id) if c.clash_institution_id else None,
        clash_institution_name=inst_b.name if inst_b else None,
        related_student_apaar=c.related_student_apaar,
        status=c.status,
        priority=c.priority,
        sla_deadline=c.sla_deadline,
        opened_by_type=c.opened_by_type,
        description=c.description,
        action_draft=c.action_draft,
        resolution_notes=c.resolution_notes,
        evidence_pack=c.evidence_pack,
        created_at=c.created_at,
        updated_at=c.updated_at
    )

@router.post("/{id}/resolve")
def resolve_case(
    id: str,
    update_data: CaseUpdate,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """Resolves an open clash/over-intake case and logs action to audit ledger."""
    c = db.query(Case).filter(Case.id == id).first()
    if not c:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")

    c.status = update_data.status or "RESOLVED"
    c.resolution_notes = update_data.resolution_notes or f"Resolved by {user.full_name} ({user.role})"
    c.updated_at = datetime.now(timezone.utc)
    db.commit()

    AuditService.append_log(
        db=db,
        action="CASE_RESOLVED",
        entity_type="CASE",
        entity_id=c.case_number,
        role=user.role,
        user_email=user.email,
        details={
            "case_number": c.case_number,
            "status": c.status,
            "notes": c.resolution_notes
        }
    )

    return {"success": True, "case_number": c.case_number, "status": c.status}
