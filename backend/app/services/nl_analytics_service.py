import re
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc

from app.models.student import Student
from app.models.institution import Institution, ProgramBranch
from app.models.case import Case
from app.models.batch import UploadBatch, ValidationFlag
from app.services.trust_score_service import TrustScoreService
from app.services.ml.ghost_student_detector import GhostStudentDetector
from app.services.ml.seat_forecaster import SeatForecaster

class SafeNLAnalyticsService:
    """
    Safe Natural Language Analytics Engine.
    Interprets analytical requests from AICTE leadership without executing un-sanitized raw SQL.
    Maps queries strictly to allowlisted, parameterized SQLAlchemy query plans.
    """

    @classmethod
    def execute_query(cls, db: Session, nl_query: str) -> Dict[str, Any]:
        q = nl_query.lower().strip()

        # Plan 1: Top institutions by student enrollment
        if any(w in q for w in ["top", "highest", "most", "largest"]) and any(w in q for w in ["institution", "college", "enrollment", "enrolment", "students"]):
            limit_match = re.search(r"\b(\d+)\b", q)
            limit = int(limit_match.group(1)) if limit_match else 5
            limit = min(max(limit, 1), 25)

            results = (
                db.query(
                    Institution.name,
                    Institution.state,
                    Institution.trust_score,
                    func.count(Student.id).label("student_count")
                )
                .join(Student, Student.institution_id == Institution.id)
                .group_by(Institution.id, Institution.name, Institution.state, Institution.trust_score)
                .order_by(desc("student_count"))
                .limit(limit)
                .all()
            )

            rows = [
                {
                    "rank": idx + 1,
                    "institution": r[0],
                    "state": r[1],
                    "trust_score": round(r[2], 1) if r[2] else 85.0,
                    "total_enrolled": r[3]
                }
                for idx, r in enumerate(results)
            ]

            return {
                "intent": "TOP_INSTITUTIONS_BY_ENROLMENT",
                "title": f"Top {limit} Institutions by Student Enrolment",
                "sql_translation": f"SELECT name, state, trust_score, COUNT(students.id) FROM institutions JOIN students GROUP BY institutions.id ORDER BY 4 DESC LIMIT {limit};",
                "columns": ["Rank", "Institution Name", "State", "Trust Score", "Total Enrolled"],
                "rows": rows,
                "chart_type": "BAR",
                "chart_key_x": "institution",
                "chart_key_y": "total_enrolled",
                "summary_insight": f"Top institution has {rows[0]['total_enrolled'] if rows else 0} verified APAAR registrations."
            }

        # Plan 2: Institutions with low trust score or at risk
        elif any(w in q for w in ["trust", "score", "risk", "poor", "low", "penalized"]):
            threshold = 70.0
            thresh_match = re.search(r"\b(\d{2})\b", q)
            if thresh_match:
                threshold = float(thresh_match.group(1))

            results = (
                db.query(Institution)
                .filter(Institution.trust_score < threshold)
                .order_by(asc(Institution.trust_score))
                .limit(10)
                .all()
            )

            rows = [
                {
                    "aicte_id": inst.aicte_id,
                    "name": inst.name,
                    "state": inst.state,
                    "trust_score": round(inst.trust_score, 1) if inst.trust_score else 0.0,
                    "audit_status": "MANDATORY ON-SITE INSPECTION" if (inst.trust_score or 100) < 60 else "VIGILANCE MONITORING"
                }
                for inst in results
            ]

            return {
                "intent": "INSTITUTIONS_AT_RISK_TRUST",
                "title": f"Institutions with Trust Score Below {threshold}",
                "sql_translation": f"SELECT aicte_id, name, state, trust_score FROM institutions WHERE trust_score < {threshold} ORDER BY trust_score ASC LIMIT 10;",
                "columns": ["AICTE ID", "Institution", "State", "Trust Score", "Vigilance Status"],
                "rows": rows,
                "chart_type": "BAR",
                "chart_key_x": "name",
                "chart_key_y": "trust_score",
                "summary_insight": f"Identified {len(rows)} colleges scoring below {threshold}. Flagged for AICTE Regional inspection."
            }

        # Plan 3: Seat capacity & near-saturation branches
        elif any(w in q for w in ["seat", "capacity", "saturation", "exhaustion", "full", "over"]):
            forecasts = SeatForecaster.forecast_all_branches(db, days_remaining=14)
            breached = [b for b in forecasts if b["risk_status"] in ["BREACHED", "HIGH_RISK_PROJECTED_BREACH", "SATURATING"]]

            rows = [
                {
                    "institution": b["institution_name"],
                    "branch": b["branch_name"],
                    "approved": b["approved_intake"],
                    "enrolled": b["current_enrolled"],
                    "utilization_pct": f"{b['current_capacity_pct']}%",
                    "status": b["risk_status"],
                    "seat_locked": "YES" if b["is_locked"] else "NO"
                }
                for b in breached[:10]
            ]

            return {
                "intent": "BRANCH_CAPACITY_EXHAUSTION",
                "title": "Branches at Risk of Capacity Breach / Quota Saturation",
                "sql_translation": "SELECT i.name, b.branch, b.approved_intake, COUNT(s.id) FROM program_branches b JOIN institutions i ... HAVING ratio > 0.85;",
                "columns": ["Institution", "Branch", "Approved Intake", "Current Enrolled", "Utilization", "Risk Status", "Seat Lock"],
                "rows": rows,
                "chart_type": "TABLE",
                "summary_insight": f"{len(rows)} branches are currently saturating or breaching AICTE intake ceilings."
            }

        # Plan 4: Demographic & Category breakdown
        elif any(w in q for w in ["category", "quota", "demographic", "reservation", "caste", "gender", "female", "male"]):
            if "gender" in q or "female" in q or "male" in q:
                res = db.query(Student.gender, func.count(Student.id)).group_by(Student.gender).all()
                rows = [{"category": r[0], "count": r[1]} for r in res]
                title = "National Gender Distribution across APAAR Registrations"
            else:
                res = db.query(Student.category, func.count(Student.id)).group_by(Student.category).all()
                rows = [{"category": r[0], "count": r[1]} for r in res]
                title = "National Category / Quota Distribution"

            return {
                "intent": "DEMOGRAPHIC_DISTRIBUTION",
                "title": title,
                "sql_translation": "SELECT category, COUNT(id) FROM students GROUP BY category ORDER BY 2 DESC;",
                "columns": ["Classification", "Student Count"],
                "rows": rows,
                "chart_type": "PIE",
                "chart_key_x": "category",
                "chart_key_y": "count",
                "summary_insight": f"Cohort categorized across {len(rows)} distinct demographic divisions."
            }

        # Plan 5: State-level student enrollment distribution
        elif any(w in q for w in ["state", "region", "haryana", "delhi", "maharashtra", "punjab", "karnataka", "tamil"]):
            res = (
                db.query(Institution.state, func.count(Student.id).label("cnt"))
                .join(Student, Student.institution_id == Institution.id)
                .group_by(Institution.state)
                .order_by(desc("cnt"))
                .all()
            )
            rows = [{"state": r[0] or "Unknown", "students": r[1]} for r in res]

            return {
                "intent": "STATE_ENROLMENT_SUMMARY",
                "title": "State-Wise Student Enrollment Aggregation",
                "sql_translation": "SELECT institutions.state, COUNT(students.id) FROM institutions JOIN students GROUP BY institutions.state ORDER BY 2 DESC;",
                "columns": ["State", "Total Verified Students"],
                "rows": rows,
                "chart_type": "BAR",
                "chart_key_x": "state",
                "chart_key_y": "students",
                "summary_insight": f"Admissions tracked across {len(rows)} states and union territories."
            }

        # Plan 6: Anomaly & Ghost Student Analysis
        elif any(w in q for w in ["anomaly", "ghost", "balaji", "isolation", "synthetic", "spike"]):
            anomalies = GhostStudentDetector.analyze_institutions(db)
            rows = [
                {
                    "institution": a["name"],
                    "state": a["state"],
                    "score": f"{a['anomaly_score']}/100",
                    "risk_tier": a["risk_tier"],
                    "surge": f"{a['surge_ratio']}x",
                    "clustering_pct": f"{a['last_day_clustering']}%"
                }
                for a in anomalies if a.get("is_anomaly", False) or a["anomaly_score"] > 60
            ]

            return {
                "intent": "ANOMALY_SUMMARY",
                "title": "Isolation Forest Ghost Student & Ingestion Anomaly Radar",
                "sql_translation": "ISOLATION_FOREST(surge_velocity, last_day_clustering, demographic_entropy, consecutive_apaar_ratio, capacity_saturation);",
                "columns": ["Institution", "State", "Anomaly Score", "Risk Tier", "Surge Velocity", "Final 72h Spike"],
                "rows": rows,
                "chart_type": "TABLE",
                "summary_insight": f"Flagged {len(rows)} institutions displaying statistical clustering or synthetic APAAR patterns."
            }

        # Fallback Plan: General System Metrics Overview
        else:
            total_students = db.query(func.count(Student.id)).scalar() or 0
            total_institutions = db.query(func.count(Institution.id)).scalar() or 0
            flagged_students = db.query(func.count(Student.id)).filter(Student.verification_status == "FLAGGED").scalar() or 0
            open_cases = db.query(func.count(Case.id)).filter(Case.status == "OPEN").scalar() or 0

            rows = [
                {"metric": "Total APAAR Registered Students", "value": f"{total_students:,}"},
                {"metric": "AICTE Approved Institutions", "value": f"{total_institutions:,}"},
                {"metric": "Cross-Institution Flagged Students", "value": f"{flagged_students:,}"},
                {"metric": "Open Compliance Dispute Cases", "value": f"{open_cases:,}"},
            ]

            return {
                "intent": "SYSTEM_OVERVIEW",
                "title": "AICTE Central Command — National Metrics Overview",
                "sql_translation": "SELECT COUNT(*) FROM students; SELECT COUNT(*) FROM institutions; SELECT COUNT(*) FROM cases WHERE status='OPEN';",
                "columns": ["Operational Metric", "Current Count"],
                "rows": rows,
                "chart_type": "METRIC",
                "summary_insight": f"Monitoring {total_students:,} APAAR IDs across {total_institutions} institutions."
            }
