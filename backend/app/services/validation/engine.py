import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from app.models.institution import Institution, ProgramBranch
from app.models.student import Student
from app.models.batch import UploadBatch, ValidationFlag
from app.models.case import Case
from app.services.validation.base_rule import BaseValidationRule, RuleSeverity, ValidationContext, ValidationIssue
from app.services.validation.rules.apaar_format_rule import ApaarFormatRule
from app.services.validation.rules.duplicate_within_institution_rule import DuplicateWithinInstitutionRule
from app.services.validation.rules.cross_institution_clash_rule import CrossInstitutionClashRule
from app.services.validation.rules.intake_capacity_rule import IntakeCapacityRule
from app.services.validation.rules.logical_consistency_rules import LogicalConsistencyRule
from app.services.audit_service import AuditService

class ValidationEngine:
    def __init__(self, rules: Optional[List[BaseValidationRule]] = None):
        self.rules = rules or [
            ApaarFormatRule(),
            DuplicateWithinInstitutionRule(),
            CrossInstitutionClashRule(),
            IntakeCapacityRule(),
            LogicalConsistencyRule(),
        ]

    def build_context(self, db: Session, institution_id: str) -> ValidationContext:
        inst = db.query(Institution).filter(Institution.id == institution_id).first()
        if not inst:
            raise ValueError(f"Institution {institution_id} not found")

        # Pre-load branch intake map
        branches = db.query(ProgramBranch).filter(ProgramBranch.institution_id == institution_id).all()
        branch_map = {
            pb.branch: {"approved": pb.approved_intake, "current": pb.enrolled_count}
            for pb in branches
        }

        return ValidationContext(
            db=db,
            institution_id=str(inst.id),
            institution_name=inst.name,
            approved_intake=inst.approved_intake,
            current_enrolment=inst.actual_enrolment,
            batch_apaar_tracker=set(),
            branch_intake_map=branch_map
        )

    def validate_record(
        self,
        record: Dict[str, Any],
        context: ValidationContext,
        row_index: Optional[int] = None
    ) -> List[ValidationIssue]:
        issues: List[ValidationIssue] = []
        for rule in self.rules:
            rule_issues = rule.validate(record, context)
            for iss in rule_issues:
                iss.row_index = row_index
                issues.append(iss)
        return issues

    def process_batch(
        self,
        db: Session,
        batch: UploadBatch,
        raw_records: List[Dict[str, Any]],
        user_email: Optional[str] = "admin@institution.edu"
    ) -> Dict[str, Any]:
        """
        Processes a full batch of records through all validation rule plugins.
        Persists flags, manages cases, and logs audit events.
        """
        context = self.build_context(db, str(batch.institution_id))
        all_issues: List[ValidationIssue] = []
        valid_count = 0
        flagged_count = 0
        clash_count = 0
        over_intake_detected = False

        for idx, rec in enumerate(raw_records):
            row_idx = idx + 1
            issues = self.validate_record(rec, context, row_index=row_idx)

            if issues:
                flagged_count += 1
                for iss in issues:
                    all_issues.append(iss)
                    
                    # Persist ValidationFlag
                    flag = ValidationFlag(
                        upload_batch_id=str(batch.id),
                        institution_id=str(batch.institution_id),
                        apaar_id=iss.student_apaar,
                        rule_code=iss.rule_code,
                        severity=iss.severity.value,
                        description=iss.message,
                        fix_suggestion=iss.fix_suggestion,
                        resolved=False
                    )
                    db.add(flag)

                    # Trigger Cross-College Clash Case
                    if iss.rule_code == "CROSS_INSTITUTION_DUPLICATE" and iss.student_apaar:
                        clash_count += 1
                        self._handle_cross_clash_case(db, batch, iss.student_apaar, iss.message)

                    if iss.rule_code == "SEAT_LOCK_BREACH":
                        over_intake_detected = True
            else:
                valid_count += 1

        # Update batch summary
        batch.total_records = len(raw_records)
        batch.processed_records = len(raw_records)
        batch.valid_records = valid_count
        batch.flagged_records = flagged_count
        batch.status = "COMPLETED"
        batch.completed_at = datetime.now(timezone.utc)
        batch.error_summary = {
            "total_issues": len(all_issues),
            "critical_issues": sum(1 for i in all_issues if i.severity == RuleSeverity.CRITICAL),
            "high_issues": sum(1 for i in all_issues if i.severity == RuleSeverity.HIGH),
            "warning_issues": sum(1 for i in all_issues if i.severity == RuleSeverity.WARNING),
            "clashes_opened": clash_count,
            "over_intake_triggered": over_intake_detected
        }

        # Update institution status if over intake triggered
        inst = db.query(Institution).filter(Institution.id == batch.institution_id).first()
        if inst and over_intake_detected:
            inst.status = "WARNING"
            inst.trust_score = max(50.0, inst.trust_score - 10.0)

        db.commit()

        # Audit log the batch processing
        AuditService.append_log(
            db=db,
            action="BATCH_VALIDATION_COMPLETED",
            entity_type="UPLOAD_BATCH",
            entity_id=str(batch.id),
            role="INSTITUTION_ADMIN",
            user_email=user_email,
            details={
                "batch_id": str(batch.id),
                "total_records": len(raw_records),
                "valid": valid_count,
                "flagged": flagged_count,
                "clashes": clash_count
            }
        )

        return {
            "batch_id": str(batch.id),
            "total_records": len(raw_records),
            "valid_records": valid_count,
            "flagged_records": flagged_count,
            "issues": [
                {
                    "row_index": i.row_index,
                    "rule_code": i.rule_code,
                    "severity": i.severity.value,
                    "student_apaar": i.student_apaar,
                    "field_name": i.field_name,
                    "message": i.message,
                    "fix_suggestion": i.fix_suggestion,
                    "auto_fixable": i.auto_fixable
                }
                for i in all_issues
            ]
        }

    def _handle_cross_clash_case(self, db: Session, batch: UploadBatch, apaar_id: str, message: str):
        """Opens real-time resolution case with SLA timer when cross-college duplicate is detected."""
        existing_student = db.query(Student).filter(
            Student.apaar_id == apaar_id,
            Student.institution_id != str(batch.institution_id)
        ).first()

        clash_inst_id = str(existing_student.institution_id) if existing_student else None
        
        # Check if active case already exists for this APAAR
        existing_case = db.query(Case).filter(
            Case.related_student_apaar == apaar_id,
            Case.status.in_(["OPEN", "IN_REVIEW"])
        ).first()

        if not existing_case:
            case_no = f"CASE-{datetime.now().year}-{str(uuid.uuid4())[:6].upper()}"
            sla = datetime.now(timezone.utc) + timedelta(hours=48)
            new_case = Case(
                case_number=case_no,
                title=f"Cross-College Dual Enrolment Clash: APAAR {apaar_id}",
                institution_id=str(batch.institution_id),
                clash_institution_id=clash_inst_id,
                related_student_apaar=apaar_id,
                status="OPEN",
                priority="URGENT",
                sla_deadline=sla,
                opened_by_type="SYSTEM",
                description=message,
                action_draft="Automated formal notice dispatched to both college registrars to verify Migration Certificate.",
                evidence_pack={
                    "apaar_id": apaar_id,
                    "reporting_institution_id": str(batch.institution_id),
                    "conflicting_institution_id": clash_inst_id,
                    "sla_hours": 48
                }
            )
            db.add(new_case)
