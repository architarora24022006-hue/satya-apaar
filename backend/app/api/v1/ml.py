from typing import Any, Dict, List, Optional
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.rbac import UserRole, get_current_user, require_roles
from app.models.case import Case
from app.models.student import Student
from app.models.institution import Institution

from app.services.ml.ghost_student_detector import GhostStudentDetector
from app.services.trust_score_service import TrustScoreService
from app.services.ml.fuzzy_matcher import FuzzyDuplicateMatcher
from app.services.ml.seat_forecaster import SeatForecaster
from app.services.audit_service import AuditService

router = APIRouter(prefix="/ml", tags=["AI & Machine Learning Engine"])

class SeatLockRequest(BaseModel):
    branch_id: str
    lock_state: bool

class OpenFuzzyCaseRequest(BaseModel):
    candidate_id: str
    record_a_id: str
    record_b_id: str
    reason: str

@router.get("/anomalies")
def get_institution_anomalies(
    db: Session = Depends(get_db)
):
    """
    Feature A: Scikit-learn Isolation Forest Anomaly Detection.
    Identifies institutions exhibiting ghost-student velocity surges,
    demographic entropy anomalies, and sequential APAAR patterns.
    """
    results = GhostStudentDetector.analyze_institutions(db)
    return results

@router.get("/anomalies/{institution_id}")
def get_single_institution_anomaly(
    institution_id: str,
    db: Session = Depends(get_db)
):
    """Detailed anomaly diagnostic report for an institution."""
    res = GhostStudentDetector.get_institution_anomaly(db, institution_id)
    if not res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Anomaly profile for institution {institution_id} not found"
        )
    return res

@router.get("/trust-scores")
def get_trust_scores(
    db: Session = Depends(get_db)
):
    """
    Feature B: Institution Trust Score Engine.
    Returns 0-100 scores with transparent 4-part mathematical breakdown:
    Data Quality + Timeliness + Anomaly Clearance + Dispute Resolution.
    """
    scores = TrustScoreService.update_all_trust_scores(db)
    return scores

@router.post("/trust-scores/recalculate")
def recalculate_trust_scores(
    db: Session = Depends(get_db)
):
    """Force recalculates and stores trust scores across all institutions."""
    scores = TrustScoreService.update_all_trust_scores(db)
    return {
        "success": True,
        "total_institutions_updated": len(scores),
        "leaderboard": scores[:10]
    }

@router.get("/fuzzy-duplicates")
def get_fuzzy_duplicate_candidates(
    similarity_threshold: float = Query(80.0, ge=50.0, le=100.0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """
    Feature C: RapidFuzz Cross-Institution Identity Duplicate Matcher.
    Detects students registered at multiple colleges with name variances,
    middle initials, or slight formatting typos.
    """
    matches = FuzzyDuplicateMatcher.find_cross_institution_duplicates(
        db=db,
        similarity_threshold=similarity_threshold,
        limit=limit
    )
    return matches

@router.post("/fuzzy-duplicates/open-case")
def open_case_for_fuzzy_duplicate(
    payload: OpenFuzzyCaseRequest,
    db: Session = Depends(get_db)
):
    """1-Click escalation: converts a fuzzy duplicate match into an official AICTE Dispute Case with SLA."""
    now = datetime.now(timezone.utc)
    student_a = db.query(Student).filter(Student.id == payload.record_a_id).first()
    student_b = db.query(Student).filter(Student.id == payload.record_b_id).first()

    inst_a_id = str(student_a.institution_id) if student_a else None
    inst_b_id = str(student_b.institution_id) if student_b else None
    apaar = student_a.apaar_id if student_a else None

    if not inst_a_id:
        first_inst = db.query(Institution).first()
        inst_a_id = str(first_inst.id) if first_inst else None

    case_num = f"CASE-{now.year}-{int(now.timestamp()) % 10000:04d}"

    new_case = Case(
        case_number=case_num,
        title=f"Probable Cross-College Identity Duplicate: {payload.candidate_id}",
        institution_id=inst_a_id,
        clash_institution_id=inst_b_id,
        related_student_apaar=apaar,
        status="OPEN",
        priority="HIGH",
        sla_deadline=now + timedelta(hours=48),
        opened_by_type="SENTINEL",
        description=f"Automated Fuzzy Matcher flagged dual-institution registration. {payload.reason}",
        evidence_pack={
            "candidate_id": payload.candidate_id,
            "record_a_id": payload.record_a_id,
            "record_b_id": payload.record_b_id,
            "reason": payload.reason
        }
    )
    db.add(new_case)
    db.commit()
    db.refresh(new_case)


    # Immutable Audit Log
    AuditService.append_log(
        db=db,
        action="CASE_CREATED",
        entity_type="CASE",
        entity_id=str(new_case.id),
        role="AICTE_ADMIN",
        details={"case_title": new_case.title, "candidate_id": payload.candidate_id}
    )

    return {
        "success": True,
        "case_id": str(new_case.id),
        "case_number": new_case.case_number,
        "message": "Formal cross-institution dispute case opened with 48h SLA countdown."
    }

@router.get("/seat-forecast")
def get_seat_forecast(
    days_remaining: int = Query(14, ge=1, le=90),
    db: Session = Depends(get_db)
):
    """
    Feature D: Predictive Seat Allocation Forecaster.
    Uses admission velocity trends to forecast intake capacity breaches
    before deadlines.
    """
    forecasts = SeatForecaster.forecast_all_branches(db, days_remaining)
    return forecasts

@router.post("/seat-lock/toggle")
def toggle_branch_seat_lock(
    payload: SeatLockRequest,
    db: Session = Depends(get_db)
):
    """
    Feature E: Real-time Seat-Lock Mechanism.
    Locks or unlocks admission intake for a program branch.
    """
    res = SeatForecaster.toggle_seat_lock(db, payload.branch_id, payload.lock_state)
    if not res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Program branch {payload.branch_id} not found"
        )

    # Immutable Audit Log
    AuditService.append_log(
        db=db,
        action="SEAT_LOCK_TOGGLED",
        entity_type="PROGRAM_BRANCH",
        entity_id=payload.branch_id,
        role="AICTE_ADMIN",
        details={"branch_id": payload.branch_id, "lock_state": payload.lock_state}
    )

    return res
