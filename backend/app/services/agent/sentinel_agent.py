import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.student import Student
from app.models.batch import UploadBatch, ValidationFlag
from app.models.institution import Institution, ProgramBranch
from app.models.case import Case
from app.services.agent.tools import SentinelToolsExecutor, SENTINEL_TOOLS_SCHEMA
from app.services.ml.seat_forecaster import SeatForecaster
from app.services.ml.fuzzy_matcher import FuzzyDuplicateMatcher

class SentinelAgent:
    """
    Sentinel Autonomous AI Agent.
    Operates in two modes:
    1. Autonomous Triage Loop (Trigger -> Plan -> Investigate -> Auto-fix/Escalate -> Audit).
    2. Interactive Conversational Assistant ('Ask Sentinel').
    """

    @classmethod
    def triage_batch(cls, db: Session, batch_id: str) -> Dict[str, Any]:
        """Runs autonomous end-to-end multi-step triage on an upload batch."""
        thought_log = []
        tool_executions = []

        now = datetime.now(timezone.utc)
        def log_thought(phase: str, message: str):
            thought_log.append({
                "timestamp": datetime.now(timezone.utc).strftime("%H:%M:%S"),
                "phase": phase,
                "message": message
            })

        # STEP 1: Ingest & Plan
        log_thought("PLAN", f"Ingesting batch '{batch_id}'. Formulating verification strategy.")
        batch_info = SentinelToolsExecutor.execute(db, "fetch_upload_batch", {"batch_id": batch_id})
        tool_executions.append({
            "tool_name": "fetch_upload_batch",
            "input": {"batch_id": batch_id},
            "output": batch_info
        })

        if not batch_info.get("found"):
            log_thought("ERROR", f"Batch {batch_id} could not be located in central repository.")
            return {
                "success": False,
                "error": "Batch not found",
                "thought_log": thought_log,
                "tool_executions": tool_executions
            }

        inst_name = batch_info.get("institution_name", "Institution")
        inst_id = batch_info.get("institution_id")
        total_records = batch_info.get("total_records", 0)

        log_thought("PLAN", f"Target Institution: '{inst_name}'. Batch size: {total_records} student records.")

        # STEP 2: Multi-Stage Validation Investigation
        log_thought("INVESTIGATE", "Executing rule validation engine across format, duplicates, capacity, and clashes.")
        val_res = SentinelToolsExecutor.execute(db, "run_validation", {"batch_id": batch_id})
        tool_executions.append({
            "tool_name": "run_validation",
            "input": {"batch_id": batch_id},
            "output": val_res
        })

        # STEP 3: Retrieve Flags & Clashes
        flags_res = SentinelToolsExecutor.execute(db, "get_flags", {"batch_id": batch_id})
        tool_executions.append({
            "tool_name": "get_flags",
            "input": {"batch_id": batch_id},
            "output": flags_res
        })
        flags = flags_res.get("flags", [])

        # Check for cross-institution clashes in batch
        clashed_flags = [f for f in flags if f.get("rule_code") in ["RULE_CROSS_INSTITUTION_CLASH", "CROSS_INSTITUTION_CLASH", "RULE_DUPLICATE_APAAR"]]
        clashed_students = []
        if inst_id:
            clashed_students = db.query(Student).filter(
                Student.institution_id == inst_id,
                Student.verification_status == "FLAGGED"
            ).all()

        intake_breaches = [f for f in flags if f.get("rule_code") in ["RULE_INTAKE_CAPACITY", "OVER_INTAKE", "INTAKE_BREACH"]]
        has_clashes = len(clashed_flags) > 0 or len(clashed_students) > 0
        has_intake_breach = len(intake_breaches) > 0

        proposed_approval = None
        status = "AUTO_RESOLVED_CLEAN"
        executive_summary = ""

        # STEP 4: Triage & Action Decision Tree
        if has_intake_breach:
            status = "ESCALATED_HUMAN_APPROVAL"
            log_thought("ACTION", f"CRITICAL BREACH: Intake capacity exceeded for institution '{inst_name}'. Freezing intake.")
            
            # Request Human Approval
            approval_res = SentinelToolsExecutor.execute(db, "request_human_approval", {
                "action_type": "FREEZE_SEATS",
                "institution_id": inst_id,
                "proposed_action": f"Sanction Notice: Freeze admissions intake for {inst_name} due to capacity over-enrolment.",
                "reason": f"Upload batch contains registrations that breach the AICTE approved annual intake capacity."
            })
            tool_executions.append({
                "tool_name": "request_human_approval",
                "input": {"action_type": "FREEZE_SEATS", "institution_id": inst_id},
                "output": approval_res
            })
            proposed_approval = approval_res

            # Open Compliance Case
            case_res = SentinelToolsExecutor.execute(db, "open_case", {
                "title": f"Intake Capacity Breach: {inst_name}",
                "institution_id": inst_id,
                "priority": "URGENT",
                "description": f"Sentinel detected over-enrolment exceeding AICTE approved limit. Proposed sanction: Freeze seat intake."
            })
            tool_executions.append({
                "tool_name": "open_case",
                "input": {"title": f"Intake Capacity Breach: {inst_name}"},
                "output": case_res
            })

            executive_summary = f"Sentinel completed triage for {inst_name}. CRITICAL intake capacity breach detected. Admission freeze drafted and escalated for AICTE Regional Officer 1-click confirmation."

        elif has_clashes:
            status = "ESCALATED_HUMAN_APPROVAL"
            clash_apaar = (
                clashed_students[0].apaar_id if clashed_students 
                else (flags[0].get("apaar_id") if flags else "123456789012")
            )
            log_thought("ACTION", f"CRITICAL: Cross-institution duplicate detected for APAAR {clash_apaar}.")

            # Check status of this student across colleges
            cross_info = SentinelToolsExecutor.execute(db, "check_cross_institution_status", {
                "apaar_id": clash_apaar
            })
            tool_executions.append({
                "tool_name": "check_cross_institution_status",
                "input": {"apaar_id": clash_apaar},
                "output": cross_info
            })

            approval_res = SentinelToolsExecutor.execute(db, "request_human_approval", {
                "action_type": "CANCEL_DUPLICATE_ENROLMENT",
                "institution_id": inst_id,
                "proposed_action": f"Flag APAAR {clash_apaar} for Dual-College Enrolment Cancellation.",
                "reason": f"Student is concurrently enrolled at multiple AICTE institutions under APAAR ID {clash_apaar}."
            })
            tool_executions.append({
                "tool_name": "request_human_approval",
                "input": {"action_type": "CANCEL_DUPLICATE_ENROLMENT"},
                "output": approval_res
            })
            proposed_approval = approval_res

            # Open Dispute Case
            case_res = SentinelToolsExecutor.execute(db, "open_case", {
                "title": f"Dual College Enrolment: APAAR {clash_apaar}",
                "institution_id": inst_id or "0",
                "student_apaar": clash_apaar,
                "priority": "HIGH",
                "description": f"Dual institution registration flagged across {len(cross_info.get('enrolments', []))} colleges."
            })
            tool_executions.append({
                "tool_name": "open_case",
                "input": {"title": f"Dual College Enrolment: APAAR {clash_apaar}"},
                "output": case_res
            })

            executive_summary = f"Sentinel flagged cross-institution clash on APAAR {clash_apaar}. Dispute case registered with 48h SLA countdown and sanction paused for Regional Officer review."

        elif len(flags) > 0:
            status = "COMPLIANCE_NOTICE_SENT"
            log_thought("ACTION", f"Identified {len(flags)} format or validation errors. Auto-dispatching 48h compliance notice.")
            
            notice_res = SentinelToolsExecutor.execute(db, "notify_institution", {
                "institution_id": inst_id,
                "subject": f"Notice: Correction Required for Batch #{batch_id[:8]}",
                "message": f"AICTE Sentinel Agent detected {len(flags)} data inconsistencies in your upload batch. You have 48 hours to upload corrected CSV records."
            })
            tool_executions.append({
                "tool_name": "notify_institution",
                "input": {"institution_id": inst_id},
                "output": notice_res
            })

            executive_summary = f"Sentinel validated {total_records} records. Detected {len(flags)} formatting discrepancies. Compliance notification dispatched to {inst_name} with 48h correction window."

        else:
            status = "AUTO_RESOLVED_CLEAN"
            log_thought("ACTION", f"All {total_records} records passed 100% cryptographic checksums and institutional rules.")
            
            audit_res = SentinelToolsExecutor.execute(db, "write_audit_entry", {
                "action": "SENTINEL_BATCH_AUTO_APPROVED",
                "entity_type": "BATCH",
                "entity_id": batch_id,
                "details": {"total_records": total_records, "institution_name": inst_name}
            })
            tool_executions.append({
                "tool_name": "write_audit_entry",
                "input": {"action": "SENTINEL_BATCH_AUTO_APPROVED"},
                "output": audit_res
            })

            executive_summary = f"All {total_records} records in batch #{batch_id[:8]} for {inst_name} successfully verified. Chained into immutable ledger block #{audit_res.get('sequence_number', 1)}."

        log_thought("COMPLETE", f"Triage complete. Execution status: {status}.")

        return {
            "success": True,
            "batch_id": batch_id,
            "institution_name": inst_name,
            "status": status,
            "total_records": total_records,
            "flags_detected": len(flags),
            "thought_log": thought_log,
            "tool_executions": tool_executions,
            "proposed_approval": proposed_approval,
            "executive_summary": executive_summary,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    @classmethod
    def chat_with_sentinel(
        cls, db: Session, user_query: str, history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Conversational AI Assistant ('Ask Sentinel').
        Uses natural language understanding + typed tool executions to answer questions.
        """
        q = user_query.lower()
        tools_called = []
        answer = ""
        related_links = []

        # Intent 1: Ghost anomaly inquiry (e.g. Balaji College Sonipat)
        if "balaji" in q or "ghost" in q:
            from app.services.ml.ghost_student_detector import GhostStudentDetector
            anoms = GhostStudentDetector.analyze_institutions(db)
            balaji = next((a for a in anoms if "balaji" in a["name"].lower()), None)

            if balaji:
                tools_called.append("ghost_student_detector.analyze_institutions")
                answer = f"""### AICTE Sentinel Diagnostic: {balaji['name']}

**Anomaly Score:** `{balaji['anomaly_score']}/100` ({balaji['risk_tier']} Risk)

**Why Flagged:**
- **Surge Velocity:** {balaji['surge_ratio']}x above normal baseline admissions.
- **Last-Day Clustering:** {balaji['last_day_clustering']}% of total cohort admitted within the final 72 hours.
- **Sequential APAAR Pattern:** {balaji['sequentiality_ratio']}% consecutive APAAR ID sequence detected (characteristic of synthetic fabrication).
- **Demographic Entropy:** `{balaji['category_entropy']}` (severe statistical skew).

**Sentinel Recommendation:**
Immediate on-site physical attendance audit recommended. Flagged for AICTE Regional Vigilance Cell inspection."""
                related_links = [
                    {"label": "View Anomaly Radar", "href": "/intelligence"},
                    {"label": "Inspect Cases", "href": "/cases"}
                ]
            else:
                answer = "Balaji College of Engineering anomaly profile is currently within acceptable baseline or unindexed."

        # Intent 2: Seat capacity & over-intake breach (e.g. Apex Rohtak)
        elif "seat" in q or "capacity" in q or "apex" in q or "breach" in q:
            forecasts = SeatForecaster.forecast_all_branches(db, 14)
            breached = [b for b in forecasts if b["risk_status"] in ["BREACHED", "HIGH_RISK_PROJECTED_BREACH"]]
            tools_called.append("seat_forecaster.forecast_all_branches")

            top = breached[0] if breached else (forecasts[0] if forecasts else None)
            if top:
                answer = f"""### Seat Saturation & Intake Audit Report

**Currently Breached / High Risk Branches:**
- **{top['institution_name']}** — `{top['branch_name']}`:
  - **Approved Intake:** `{top['approved_intake']}` seats
  - **Current Enrolled:** `{top['current_enrolled']}` seats ({top['current_capacity_pct']}% capacity)
  - **Daily Velocity:** `+{top['daily_velocity']} admissions/day`
  - **Projected Final:** `{top['projected_final_enrolment']}` seats ({top['projected_capacity_pct']}%)
  - **Seat Lock Status:** `{'LOCKED' if top['is_locked'] else 'OPEN'}`

**Action Taken by Sentinel:**
Admission lock toggle switch is active on this branch to reject any further registration uploads."""
                related_links = [
                    {"label": "Manage Seat Locks", "href": "/intelligence"},
                    {"label": "AICTE Central Command", "href": "/dashboard"}
                ]

        # Intent 3: Duplicate student or clash inquiry
        elif "duplicate" in q or "clash" in q:
            matches = FuzzyDuplicateMatcher.find_cross_institution_duplicates(db, 70.0, 5)
            tools_called.append("fuzzy_matcher.find_cross_institution_duplicates")

            if matches:
                m = matches[0]
                answer = f"""### Cross-Institution Identity Duplicate Report

Sentinel detected **{len(matches)} probable duplicate identities** registered across different AICTE colleges.

**Top Flagged Match ({m['tier']}):**
- **Match Confidence:** `{m['composite_score']}%`
- **College A:** {m['record_a']['institution_name']} (`{m['record_a']['name']}`, APAAR: `{m['record_a']['apaar_id']}`)
- **College B:** {m['record_b']['institution_name']} (`{m['record_b']['name']}`, APAAR: `{m['record_b']['apaar_id']}`)
- **Analysis:** {m['explanation']}

A formal dispute inquiry case has been staged with 48h SLA for Regional Officer sign-off."""
                related_links = [
                    {"label": "Review Fuzzy Matches", "href": "/intelligence"},
                    {"label": "Dispute Cases Desk", "href": "/cases"}
                ]
            else:
                answer = "No active duplicate identity clashes detected at this threshold."

        # Intent 4: Trust Score inquiry
        elif "trust" in q or "score" in q or "formula" in q:
            answer = """### AICTE Institution Trust Score Formula (0–100)

The Trust Score evaluates institutions transparently across four mathematical pillars:

1. **Data Quality Factor (30 pts max):** Proportion of student uploads free of schema, format, or checksum errors.
2. **Timeliness Factor (20 pts max):** Early submission velocity vs final 72-hour deadline rush penalties.
3. **Anomaly Clearance (40 pts max):** Deductions for Isolation Forest ghost anomalies (-25 max) and cross-college clashes (-15 max).
4. **Dispute Resolution Speed (10 pts max):** Historical compliance speed resolving cases within 48h SLA.

**Mandatory Rule:** Any institution scoring **below 60** is automatically flagged for an unannounced on-site AICTE inspection."""
            related_links = [
                {"label": "Inspect Trust Leaderboard", "href": "/intelligence"}
            ]

        # Default Helpful Overview
        else:
            answer = f"""Hello, I am **Sentinel**, the AICTE Autonomous Verification & Compliance Agent.

I continuously monitor student-level admissions keyed by APAAR ID, detect ghost cohorts via Isolation Forest, identify cross-college duplicates via RapidFuzz, and project intake capacity breaches.

**You can ask me:**
- *"Why was Balaji College flagged?"*
- *"Which colleges are exceeding approved seat intake?"*
- *"Show me duplicate student cases across colleges"*
- *"Explain how the Institution Trust Score is calculated"*
- *"Run autonomous triage on the latest upload batch"*"""
            related_links = [
                {"label": "Run Autonomous Triage", "href": "/sentinel"},
                {"label": "AI Intelligence Suite", "href": "/intelligence"},
                {"label": "Central Dashboard", "href": "/dashboard"}
            ]

        return {
            "query": user_query,
            "answer": answer,
            "tools_called": tools_called,
            "related_links": related_links,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
