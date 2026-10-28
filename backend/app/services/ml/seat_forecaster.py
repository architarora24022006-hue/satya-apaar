from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.institution import Institution, ProgramBranch
from app.models.student import Student

class SeatForecaster:
    """
    Predictive Seat Allocation & Intake Saturation Forecaster.
    Uses admission velocity trends to forecast intake capacity breaches
    before deadlines, and manages automated seat locking.
    """

    @classmethod
    def forecast_all_branches(
        cls, db: Session, days_remaining: int = 14
    ) -> List[Dict[str, Any]]:
        branches = db.query(ProgramBranch).all()
        results = []

        now = datetime.now(timezone.utc)
        two_weeks_ago = (now - timedelta(days=14)).date()

        for branch in branches:
            inst = branch.institution
            approved = branch.approved_intake
            
            # Count current students enrolled
            current_enrolled = db.query(func.count(Student.id)).filter(
                Student.program_branch_id == branch.id
            ).scalar() or 0

            # Fallback if program_branch_id wasn't linked during raw CSV ingestion
            if current_enrolled == 0 and inst:
                current_enrolled = db.query(func.count(Student.id)).filter(
                    Student.institution_id == inst.id,
                    Student.branch.ilike(f"%{branch.branch}%")
                ).scalar() or 0

            current_pct = round((current_enrolled / max(approved, 1)) * 100, 1)

            # Velocity in past 14 days
            recent_count = db.query(func.count(Student.id)).filter(
                Student.institution_id == branch.institution_id,
                Student.branch.ilike(f"%{branch.branch}%"),
                Student.admission_date >= two_weeks_ago
            ).scalar() or 0

            daily_velocity = round(recent_count / 14.0, 2)
            if daily_velocity == 0 and current_enrolled > 0:
                daily_velocity = round(current_enrolled / 45.0, 2) # Baseline velocity estimate

            projected_enrolment = int(round(current_enrolled + (daily_velocity * days_remaining)))
            projected_pct = round((projected_enrolment / max(approved, 1)) * 100, 1)

            remaining_seats = approved - current_enrolled

            if current_enrolled > approved:
                status = "BREACHED"
                days_to_breach = 0
                recommendation = f"Mandatory AICTE seat lock active. Disallow further registrations for {branch.branch}."
            elif projected_enrolment > approved:
                status = "HIGH_RISK_PROJECTED_BREACH"
                days_to_breach = int(max(1, remaining_seats / max(daily_velocity, 0.1)))
                recommendation = f"Projected to exceed approved quota by {projected_enrolment - approved} seats in {days_to_breach} days."
            elif current_pct >= 85.0 or projected_pct >= 90.0:
                status = "NEAR_CAPACITY_WARNING"
                days_to_breach = int(max(1, remaining_seats / max(daily_velocity, 0.1)))
                recommendation = f"Approaching quota saturation ({current_pct}% occupied). Monitor daily admissions."
            else:
                status = "STABLE"
                days_to_breach = None
                recommendation = "Capacity healthy. Enrolment velocity within approved statistical tolerance."

            # Auto-lock if at or over capacity
            is_locked = bool(branch.is_locked or current_enrolled >= approved)

            results.append({
                "branch_id": str(branch.id),
                "institution_id": str(branch.institution_id),
                "institution_name": inst.name if inst else "Unknown",
                "institution_aicte_id": inst.aicte_id if inst else "1-00000000",
                "program_name": branch.program,
                "branch_name": branch.branch,
                "approved_intake": approved,
                "current_enrolled": current_enrolled,
                "current_capacity_pct": current_pct,
                "daily_velocity": daily_velocity,
                "projected_final_enrolment": projected_enrolment,
                "projected_capacity_pct": projected_pct,
                "days_to_breach": days_to_breach,
                "risk_status": status,
                "is_locked": is_locked,
                "recommendation": recommendation,
                "analyzed_at": now.isoformat()
            })

        # Sort highest risk and saturation first
        results.sort(key=lambda x: (x["current_capacity_pct"], x["projected_capacity_pct"]), reverse=True)
        return results

    @classmethod
    def toggle_seat_lock(cls, db: Session, branch_id: str, lock_state: bool) -> Optional[Dict[str, Any]]:
        branch = db.query(ProgramBranch).filter(ProgramBranch.id == branch_id).first()
        if not branch:
            return None

        branch.is_locked = lock_state
        db.commit()
        db.refresh(branch)

        return {
            "branch_id": str(branch.id),
            "branch_name": branch.branch,
            "institution_name": branch.institution.name if branch.institution else "College",
            "is_locked": branch.is_locked,
            "message": f"Seat allocation for {branch.branch} {'LOCKED' if lock_state else 'UNLOCKED'}."
        }

