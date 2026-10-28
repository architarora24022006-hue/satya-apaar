from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.core.rbac import UserRole, get_current_user, require_roles
from app.models.institution import Institution, ProgramBranch, InstitutionTrustHistory
from app.models.student import Student
from app.models.batch import ValidationFlag
from app.schemas.institution import InstitutionResponse, InstitutionDetailResponse, TrustScoreBreakdown

router = APIRouter(prefix="/institutions", tags=["Institutions & Monitoring"])

@router.get("/", response_model=List[InstitutionResponse])
def list_institutions(
    state: Optional[str] = None,
    region: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """Lists institutions with search and geographic filters."""
    query = db.query(Institution)

    # Institution admin restricted to own college
    if user.role == UserRole.INSTITUTION_ADMIN.value and user.institution_id:
        query = query.filter(Institution.id == user.institution_id)
    else:
        if state:
            query = query.filter(Institution.state.ilike(f"%{state}%"))
        if region:
            query = query.filter(Institution.region.ilike(f"%{region}%"))
        if status_filter:
            query = query.filter(Institution.status == status_filter.upper())
        if search:
            query = query.filter(
                (Institution.name.ilike(f"%{search}%")) |
                (Institution.aicte_id.ilike(f"%{search}%")) |
                (Institution.code.ilike(f"%{search}%"))
            )

    institutions = query.order_by(Institution.name.asc()).offset(offset).limit(limit).all()
    
    results = []
    for inst in institutions:
        utilization = round((inst.actual_enrolment / inst.approved_intake * 100), 1) if inst.approved_intake > 0 else 0.0
        results.append(InstitutionResponse(
            id=str(inst.id),
            aicte_id=inst.aicte_id,
            name=inst.name,
            code=inst.code,
            state=inst.state,
            region=inst.region,
            type=inst.type,
            trust_score=round(inst.trust_score, 1),
            approved_intake=inst.approved_intake,
            actual_enrolment=inst.actual_enrolment,
            supernumerary_intake=inst.supernumerary_intake,
            status=inst.status,
            contact_email=inst.contact_email,
            phone=inst.phone,
            utilization_rate=utilization
        ))
    return results

@router.get("/stats/overview")
def get_national_overview_stats(db: Session = Depends(get_db), user = Depends(get_current_user)):
    """Computes national aggregate statistics for AICTE and Regional dashboards."""
    total_insts = db.query(Institution).count()
    total_approved = db.query(func.sum(Institution.approved_intake)).scalar() or 0
    total_enrolled = db.query(func.sum(Institution.actual_enrolment)).scalar() or 0
    avg_trust = db.query(func.avg(Institution.trust_score)).scalar() or 90.0
    
    flagged_colleges = db.query(Institution).filter(
        Institution.status.in_(["WARNING", "LOCKED", "UNDER_AUDIT"])
    ).count()

    total_flags = db.query(ValidationFlag).filter(ValidationFlag.resolved == False).count()
    critical_flags = db.query(ValidationFlag).filter(
        ValidationFlag.resolved == False,
        ValidationFlag.severity == "CRITICAL"
    ).count()

    # State-wise distribution
    state_breakdown = db.query(
        Institution.state,
        func.count(Institution.id).label("colleges"),
        func.sum(Institution.approved_intake).label("total_intake"),
        func.sum(Institution.actual_enrolment).label("total_enrolled")
    ).group_by(Institution.state).all()

    state_stats = []
    for s in state_breakdown:
        rate = round((s.total_enrolled / s.total_intake * 100), 1) if s.total_intake else 0
        state_stats.append({
            "state": s.state,
            "colleges": s.colleges,
            "intake": s.total_intake or 0,
            "enrolment": s.total_enrolled or 0,
            "fill_rate": rate
        })

    return {
        "total_institutions": total_insts,
        "total_approved_intake": total_approved,
        "total_actual_enrolment": total_enrolled,
        "overall_fill_rate": round((total_enrolled / total_approved * 100), 1) if total_approved else 0,
        "average_trust_score": round(float(avg_trust), 1),
        "flagged_institutions_count": flagged_colleges,
        "active_validation_flags": total_flags,
        "critical_violations": critical_flags,
        "state_stats": state_stats
    }

@router.get("/{id}", response_model=InstitutionDetailResponse)
def get_institution_detail(id: str, db: Session = Depends(get_db), user = Depends(get_current_user)):
    """Retrieves full institution profile with academic programs and branches."""
    inst = db.query(Institution).filter(Institution.id == id).first()
    if not inst:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Institution not found")
    
    # Institution admin can only see own institution
    if user.role == UserRole.INSTITUTION_ADMIN.value and user.institution_id != str(inst.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to other institution data")

    programs = db.query(ProgramBranch).filter(ProgramBranch.institution_id == str(inst.id)).all()
    
    utilization = round((inst.actual_enrolment / inst.approved_intake * 100), 1) if inst.approved_intake > 0 else 0.0

    return InstitutionDetailResponse(
        id=str(inst.id),
        aicte_id=inst.aicte_id,
        name=inst.name,
        code=inst.code,
        state=inst.state,
        region=inst.region,
        type=inst.type,
        trust_score=round(inst.trust_score, 1),
        approved_intake=inst.approved_intake,
        actual_enrolment=inst.actual_enrolment,
        supernumerary_intake=inst.supernumerary_intake,
        status=inst.status,
        contact_email=inst.contact_email,
        phone=inst.phone,
        utilization_rate=utilization,
        programs=[
            {
                "id": str(p.id),
                "program": p.program,
                "branch": p.branch,
                "academic_year": p.academic_year,
                "approved_intake": p.approved_intake,
                "enrolled_count": p.enrolled_count,
                "supernumerary_intake": p.supernumerary_intake
            }
            for p in programs
        ],
        created_at=inst.created_at,
        updated_at=inst.updated_at
    )
