from typing import Any, Dict, List
from sqlalchemy.orm import Session

from app.models.student import Student
from app.services.validation.base_rule import BaseValidationRule, RuleSeverity, ValidationContext, ValidationIssue

class DuplicateWithinInstitutionRule(BaseValidationRule):
    rule_code = "DUPLICATE_WITHIN_INSTITUTION"
    rule_name = "Within-College Duplicate Enrolment Rule"
    severity = RuleSeverity.HIGH

    def validate(self, record: Dict[str, Any], context: ValidationContext) -> List[ValidationIssue]:
        issues: List[ValidationIssue] = []
        apaar_id = str(record.get("apaar_id", "")).strip().replace(" ", "").replace("-", "")
        if not apaar_id or len(apaar_id) != 12:
            return issues

        # 1. Check in-batch duplicate
        if apaar_id in context.batch_apaar_tracker:
            issues.append(ValidationIssue(
                rule_code="BATCH_DUPLICATE_APAAR",
                severity=RuleSeverity.HIGH,
                field_name="apaar_id",
                student_apaar=apaar_id,
                message=f"Duplicate student record: APAAR ID {apaar_id} appears multiple times within this uploaded batch.",
                fix_suggestion="Remove redundant duplicate row before final submission."
            ))
        else:
            context.batch_apaar_tracker.add(apaar_id)

        # 2. Check existing student in DB for the same institution
        existing_student = context.db.query(Student).filter(
            Student.apaar_id == apaar_id,
            Student.institution_id == context.institution_id
        ).first()

        if existing_student:
            issues.append(ValidationIssue(
                rule_code="PRE_EXISTING_STUDENT_DUPLICATE",
                severity=RuleSeverity.HIGH,
                field_name="apaar_id",
                student_apaar=apaar_id,
                message=f"Student with APAAR ID {apaar_id} ({existing_student.get_decrypted_name()}) is already actively registered in {context.institution_name}.",
                fix_suggestion="Verify whether this is a promotion/year advancement or a duplicate entry."
            ))

        return issues
