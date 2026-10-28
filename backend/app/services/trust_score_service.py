from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.institution import Institution, InstitutionTrustHistory, ProgramBranch
from app.models.student import Student
from app.models.case import Case
from app.services.ml.ghost_student_detector import GhostStudentDetector

class TrustScoreService:
    """
    Institution Trust Score Engine.
    Computes a transparent 0-100 score with exact breakdown across:
    1. Data Quality (30 pts max)
    2. Timeliness (20 pts max)
    3. Anomaly Clearance (40 pts max)
    4. Dispute Resolution Speed (10 pts max)
    """

    @classmethod
    def calculate_institution_trust(
        cls, db: Session, institution: Institution, anomaly_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        students = db.query(Student).filter(Student.institution_id == institution.id).all()
        total_students = len(students)

        # 1. Data Quality (Max 30 pts)
        if total_students > 0:
            validated_students = sum(1 for s in students if s.verification_status in ["VALIDATED", "VERIFIED"])
            valid_ratio = validated_students / total_students
            data_quality_pts = round(valid_ratio * 30.0, 1)
        else:
            data_quality_pts = 25.0

        # 2. Timeliness (Max 20 pts)
        if anomaly_data:
            last_day_pct = anomaly_data.get("last_day_clustering", 20.0)
            if last_day_pct < 25.0:
                timeliness_pts = 20.0
            elif last_day_pct < 50.0:
                timeliness_pts = 15.0
            elif last_day_pct < 75.0:
                timeliness_pts = 10.0
            else:
                timeliness_pts = 5.0
        else:
            timeliness_pts = 18.0

        # 3. Anomaly Clearance (Max 40 pts)
        # Deduct for ghost anomalies, intake breaches, and cross-college clashes
        anomaly_pts = 40.0
        if anomaly_data:
            anomaly_score = anomaly_data.get("anomaly_score", 20.0)
            # Deduct proportionally to anomaly score
            anomaly_deduction = (anomaly_score / 100.0) * 25.0
            anomaly_pts -= anomaly_deduction

            # Intake breach extra penalty
            if anomaly_data.get("intake_saturation", 0.8) > 1.0:
                anomaly_pts -= 10.0

        # Cross-college clash penalties
        clashed_count = sum(1 for s in students if s.verification_status == "FLAGGED")
        clash_deduction = min(15.0, clashed_count * 3.0)
        anomaly_pts = max(5.0, anomaly_pts - clash_deduction)
        anomaly_pts = round(anomaly_pts, 1)

        # 4. Dispute Resolution (Max 10 pts)
        cases = db.query(Case).filter(Case.institution_id == institution.id).all()
        if not cases:
            resolution_pts = 10.0
        else:
            resolved_cases = sum(1 for c in cases if c.status == "RESOLVED")
            resolution_pts = round((resolved_cases / len(cases)) * 10.0, 1)

        total_score = round(min(100.0, max(15.0, data_quality_pts + timeliness_pts + anomaly_pts + resolution_pts)), 1)

        is_flagged_for_audit = total_score < 60.0

        breakdown = {
            "data_quality_pts": data_quality_pts,
            "data_quality_max": 30.0,
            "timeliness_pts": timeliness_pts,
            "timeliness_max": 20.0,
            "anomaly_pts": anomaly_pts,
            "anomaly_max": 40.0,
            "resolution_pts": resolution_pts,
            "resolution_max": 10.0,
            "total_score": total_score,
            "is_flagged_for_audit": is_flagged_for_audit,
            "formula_explanation": "Trust Score = Data Quality (30) + Timeliness (20) + Anomaly Clearance (40) + Dispute Resolution (10)"
        }

        return breakdown

    @classmethod
    def update_all_trust_scores(cls, db: Session) -> List[Dict[str, Any]]:
        institutions = db.query(Institution).all()
        anomalies_map = {a["institution_id"]: a for a in GhostStudentDetector.analyze_institutions(db)}

        leaderboard = []
        now = datetime.now(timezone.utc)

        for inst in institutions:
            anom = anomalies_map.get(str(inst.id))
            breakdown = cls.calculate_institution_trust(db, inst, anom)

            old_score = inst.trust_score
            new_score = breakdown["total_score"]
            inst.trust_score = new_score

            # Record history
            hist = InstitutionTrustHistory(
                institution_id=inst.id,
                score=new_score,
                data_quality_factor=round(breakdown["data_quality_pts"] / 30.0, 2),
                timeliness_factor=round(breakdown["timeliness_pts"] / 20.0, 2),
                anomaly_penalty=round(40.0 - breakdown["anomaly_pts"], 1),
                resolution_speed_factor=round(breakdown["resolution_pts"] / 10.0, 2),
                recorded_at=now
            )
            db.add(hist)

            leaderboard.append({
                "institution_id": str(inst.id),
                "aicte_id": inst.aicte_id,
                "name": inst.name,
                "state": inst.state,
                "city": inst.address or inst.state,
                "trust_score": new_score,

                "previous_score": old_score,
                "is_flagged_for_audit": breakdown["is_flagged_for_audit"],
                "breakdown": breakdown
            })

        db.commit()
        # Sort leaderboard descending
        leaderboard.sort(key=lambda x: x["trust_score"], reverse=True)
        return leaderboard
