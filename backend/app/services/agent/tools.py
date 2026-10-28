import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.student import Student
from app.models.batch import UploadBatch, ValidationFlag
from app.models.institution import Institution, ProgramBranch

from app.models.case import Case
from app.services.audit_service import AuditService
from app.services.validation.engine import ValidationEngine
from app.services.ml.fuzzy_matcher import FuzzyDuplicateMatcher
from app.services.ml.seat_forecaster import SeatForecaster

# Anthropic Tool Schemas
SENTINEL_TOOLS_SCHEMA = [
    {
        "name": "fetch_upload_batch",
        "description": "Fetches metadata, student count, and processing status of an uploaded student batch.",
        "input_schema": {
            "type": "object",
            "properties": {
                "batch_id": {"type": "string", "description": "The unique ID or filename of the upload batch"}
            },
            "required": ["batch_id"]
        }
    },
    {
        "name": "run_validation",
        "description": "Runs the multi-stage AICTE validation engine on an upload batch.",
        "input_schema": {
            "type": "object",
            "properties": {
                "batch_id": {"type": "string", "description": "ID of the batch to validate"}
            },
            "required": ["batch_id"]
        }
    },
    {
        "name": "get_flags",
        "description": "Retrieves active validation flags (format errors, duplicates, capacity breaches) for a batch or college.",
        "input_schema": {
            "type": "object",
            "properties": {
                "batch_id": {"type": "string", "description": "Optional batch ID to filter flags"},
                "institution_id": {"type": "string", "description": "Optional institution ID"}
            }
        }
    },
    {
        "name": "fuzzy_match_students",
        "description": "Uses Rapidfuzz token sort ratio to detect cross-institution duplicate registrations under name/DOB variations.",
        "input_schema": {
            "type": "object",
            "properties": {
                "similarity_threshold": {"type": "number", "description": "Similarity percentage (default 75.0)"}
            }
        }
    },
    {
        "name": "check_cross_institution_status",
        "description": "Checks if an APAAR ID is registered at another AICTE-approved institution.",
        "input_schema": {
            "type": "object",
            "properties": {
                "apaar_id": {"type": "string", "description": "12-digit student APAAR ID"}
            },
            "required": ["apaar_id"]
        }
    },
    {
        "name": "forecast_seats",
        "description": "Forecasts intake quota saturation and detects capacity breaches for an institution and branch.",
        "input_schema": {
            "type": "object",
            "properties": {
                "institution_id": {"type": "string", "description": "ID of the institution to check"},
                "days_remaining": {"type": "integer", "description": "Days until admission close (default 14)"}
            },
            "required": ["institution_id"]
        }
    },
    {
        "name": "open_case",
        "description": "Creates an official AICTE dispute or compliance investigation Case with SLA countdown.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Title of the case"},
                "institution_id": {"type": "string", "description": "Target institution ID"},
                "clash_institution_id": {"type": "string", "description": "Secondary clashing institution ID if applicable"},
                "student_apaar": {"type": "string", "description": "Associated student APAAR ID if applicable"},
                "priority": {"type": "string", "enum": ["LOW", "MEDIUM", "HIGH", "URGENT"]},
                "description": {"type": "string", "description": "Detailed evidence and investigation context"}
            },
            "required": ["title", "institution_id", "description"]
        }
    },
    {
        "name": "notify_institution",
        "description": "Dispatches a simulated AICTE compliance notice to the institution's official contact.",
        "input_schema": {
            "type": "object",
            "properties": {
                "institution_id": {"type": "string", "description": "Target institution ID"},
                "subject": {"type": "string", "description": "Notice subject"},
                "message": {"type": "string", "description": "Content of the compliance notice"}
            },
            "required": ["institution_id", "subject", "message"]
        }
    },
    {
        "name": "request_human_approval",
        "description": "Submits a high-stakes sanction (seat freeze, enrolment cancellation) for AICTE Regional Officer approval.",
        "input_schema": {
            "type": "object",
            "properties": {
                "action_type": {"type": "string", "description": "e.g. FREEZE_SEATS, CANCEL_DUPLICATE, SANCTION_INSTITUTION"},
                "institution_id": {"type": "string", "description": "Target institution ID"},
                "proposed_action": {"type": "string", "description": "Precise action to execute upon approval"},
                "reason": {"type": "string", "description": "Justification and evidence summary"}
            },
            "required": ["action_type", "institution_id", "proposed_action", "reason"]
        }
    },
    {
        "name": "write_audit_entry",
        "description": "Appends an immutable SHA-256 chained entry into the cryptographic audit trail.",
        "input_schema": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "description": "Name of the audited action"},
                "entity_type": {"type": "string", "description": "Type of entity (BATCH, STUDENT, CASE)"},
                "entity_id": {"type": "string", "description": "Entity identifier"},
                "details": {"type": "object", "description": "JSON details to anchor into the block"}
            },
            "required": ["action", "entity_type", "entity_id", "details"]
        }
    }
]

class SentinelToolsExecutor:
    """Executes Sentinel agent typed tools against the database and ML services."""

    @classmethod
    def execute(cls, db: Session, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        handler = getattr(cls, f"_tool_{tool_name}", None)
        if not handler:
            return {"error": f"Tool '{tool_name}' not implemented by Sentinel"}
        try:
            return handler(db, args)
        except Exception as e:
            return {"error": f"Error executing tool '{tool_name}': {str(e)}"}

    @classmethod
    def _tool_fetch_upload_batch(cls, db: Session, args: Dict[str, Any]) -> Dict[str, Any]:
        batch_id = args.get("batch_id")
        batch = db.query(UploadBatch).filter(
            (UploadBatch.id == batch_id) | (UploadBatch.filename.ilike(f"%{batch_id}%"))
        ).first()

        if not batch:
            # Return demo fallback batch if not found directly
            batch = db.query(UploadBatch).order_by(UploadBatch.created_at.desc()).first()
            if not batch:
                return {"found": False, "message": "No upload batches found in repository."}

        inst = db.query(Institution).filter(Institution.id == batch.institution_id).first()

        return {
            "found": True,
            "batch_id": str(batch.id),
            "filename": batch.filename,
            "institution_id": str(batch.institution_id),
            "institution_name": inst.name if inst else "Unknown",
            "status": batch.status,
            "total_records": batch.total_records,
            "valid_records": batch.valid_records,
            "invalid_records": max(0, (batch.total_records or 0) - (batch.valid_records or 0)),
            "flagged_records": batch.flagged_records,
            "uploaded_at": batch.created_at.isoformat()
        }

    @classmethod
    def _tool_run_validation(cls, db: Session, args: Dict[str, Any]) -> Dict[str, Any]:
        batch_id = args.get("batch_id")
        batch = db.query(UploadBatch).filter(UploadBatch.id == batch_id).first()
        if not batch:
            batch = db.query(UploadBatch).first()

        if not batch:
            return {"error": "No batch available to validate"}

        summary = ValidationEngine.validate_batch(db, str(batch.id))
        return {
            "batch_id": str(batch.id),
            "validation_summary": summary
        }

    @classmethod
    def _tool_get_flags(cls, db: Session, args: Dict[str, Any]) -> Dict[str, Any]:
        query = db.query(ValidationFlag)
        batch_id = args.get("batch_id")
        if batch_id:
            query = query.filter(ValidationFlag.upload_batch_id == batch_id)
        
        flags = query.limit(20).all()
        return {
            "total_flags_retrieved": len(flags),
            "flags": [
                {
                    "flag_id": str(f.id),
                    "rule_code": f.rule_code,
                    "severity": f.severity,
                    "message": f.description,
                    "fix_recommendation": f.fix_suggestion,
                    "status": "RESOLVED" if f.resolved else "OPEN"
                }
                for f in flags
            ]
        }

    @classmethod
    def _tool_fuzzy_match_students(cls, db: Session, args: Dict[str, Any]) -> Dict[str, Any]:
        threshold = args.get("similarity_threshold", 75.0)
        matches = FuzzyDuplicateMatcher.find_cross_institution_duplicates(
            db, similarity_threshold=threshold, limit=10
        )
        return {
            "threshold": threshold,
            "matches_found": len(matches),
            "candidates": matches
        }

    @classmethod
    def _tool_check_cross_institution_status(cls, db: Session, args: Dict[str, Any]) -> Dict[str, Any]:
        apaar = args.get("apaar_id", "").replace("-", "").strip()
        students = db.query(Student).filter(Student.apaar_id == apaar).all()

        enrolments = []
        for s in students:
            enrolments.append({
                "student_id": str(s.id),
                "institution_id": str(s.institution_id),
                "institution_name": s.institution.name if s.institution else "College",
                "branch": s.branch,
                "status": s.verification_status,
                "admission_date": s.admission_date.isoformat() if s.admission_date else None
            })

        is_clash = len(enrolments) > 1
        return {
            "apaar_id": apaar,
            "is_cross_institution_clash": is_clash,
            "total_institutions_enrolled": len(enrolments),
            "enrolments": enrolments
        }

    @classmethod
    def _tool_forecast_seats(cls, db: Session, args: Dict[str, Any]) -> Dict[str, Any]:
        inst_id = args.get("institution_id")
        days = args.get("days_remaining", 14)
        all_forecasts = SeatForecaster.forecast_all_branches(db, days)
        
        filtered = [f for f in all_forecasts if f["institution_id"] == inst_id or inst_id in f["institution_aicte_id"]]
        if not filtered:
            filtered = all_forecasts[:3]

        return {
            "institution_id": inst_id,
            "forecast_horizon_days": days,
            "branches": filtered
        }

    @classmethod
    def _tool_open_case(cls, db: Session, args: Dict[str, Any]) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        case_num = f"CASE-{now.year}-{int(now.timestamp()) % 10000:04d}"

        new_case = Case(
            case_number=case_num,
            title=args.get("title", "AICTE Compliance Inquiry"),
            institution_id=args.get("institution_id"),
            clash_institution_id=args.get("clash_institution_id"),
            related_student_apaar=args.get("student_apaar"),
            status="OPEN",
            priority=args.get("priority", "HIGH"),
            sla_deadline=now + timedelta(hours=48),
            opened_by_type="SENTINEL",
            description=args.get("description", "Opened by Sentinel AI Agent."),
            evidence_pack=args
        )
        db.add(new_case)
        db.commit()
        db.refresh(new_case)

        AuditService.append_log(
            db=db,
            action="SENTINEL_OPENED_CASE",
            entity_type="CASE",
            entity_id=str(new_case.id),
            role="SENTINEL_AGENT",
            details={"case_number": case_num, "title": new_case.title}
        )

        return {
            "case_id": str(new_case.id),
            "case_number": case_num,
            "status": "OPEN",
            "sla_deadline": new_case.sla_deadline.isoformat(),
            "message": f"Case {case_num} successfully opened with 48h resolution SLA."
        }

    @classmethod
    def _tool_notify_institution(cls, db: Session, args: Dict[str, Any]) -> Dict[str, Any]:
        inst_id = args.get("institution_id")
        inst = db.query(Institution).filter(Institution.id == inst_id).first()
        target_name = inst.name if inst else f"Institution #{inst_id}"
        email = inst.contact_email if inst and inst.contact_email else "admin@institution.edu.in"

        AuditService.append_log(
            db=db,
            action="INSTITUTION_NOTIFIED",
            entity_type="INSTITUTION",
            entity_id=inst_id,
            role="SENTINEL_AGENT",
            details={
                "subject": args.get("subject"),
                "recipient_email": email,
                "message_preview": args.get("message")[:100]
            }
        )

        return {
            "delivered": True,
            "target_institution": target_name,
            "recipient_email": email,
            "subject": args.get("subject"),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    @classmethod
    def _tool_request_human_approval(cls, db: Session, args: Dict[str, Any]) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        approval_id = f"APPR-{int(now.timestamp()) % 10000:04d}"

        # Create or link to a PENDING_APPROVAL Case
        case = Case(
            case_number=approval_id,
            title=f"APPROVAL REQUIRED: {args.get('action_type')} for {args.get('institution_id')}",
            institution_id=args.get("institution_id"),
            status="PENDING_APPROVAL",
            priority="URGENT",
            sla_deadline=now + timedelta(hours=24),
            opened_by_type="SENTINEL",
            description=args.get("reason", "Action requires AICTE Regional Officer approval."),
            action_draft=args.get("proposed_action"),
            evidence_pack=args
        )
        db.add(case)
        db.commit()
        db.refresh(case)

        AuditService.append_log(
            db=db,
            action="APPROVAL_REQUESTED",
            entity_type="APPROVAL",
            entity_id=approval_id,
            role="SENTINEL_AGENT",
            details=args
        )

        return {
            "approval_id": approval_id,
            "status": "PENDING_APPROVAL",
            "action_type": args.get("action_type"),
            "proposed_action": args.get("proposed_action"),
            "reason": args.get("reason"),
            "case_id": str(case.id),
            "message": "Sanction drafted. Paused for AICTE Regional Officer 1-click confirmation."
        }

    @classmethod
    def _tool_write_audit_entry(cls, db: Session, args: Dict[str, Any]) -> Dict[str, Any]:
        entry = AuditService.append_log(
            db=db,
            action=args.get("action", "SENTINEL_ACTION"),
            entity_type=args.get("entity_type", "SYSTEM"),
            entity_id=args.get("entity_id", "0"),
            role="SENTINEL_AGENT",
            details=args.get("details", {})
        )
        return {
            "success": True,
            "sequence_number": entry.sequence_number,
            "block_hash": entry.current_hash,
            "message": f"Action chained into immutable audit block #{entry.sequence_number}"
        }
