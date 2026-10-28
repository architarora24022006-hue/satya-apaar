from typing import Any, Dict, List
from sqlalchemy.orm import Session

from app.models.student import Student
from app.models.institution import Institution
from app.services.validation.base_rule import BaseValidationRule, RuleSeverity, ValidationContext, ValidationIssue

class CrossInstitutionClashRule(BaseValidationRule):
    rule_code = "CROSS_INSTITUTION_DUPLICATE"
    rule_name = "Cross-Institution Dual Enrolment Clash Rule"
    severity = RuleSeverity.CRITICAL

    def validate(self, record: Dict[str, Any], context: ValidationContext) -> List[ValidationIssue]:
        issues: List[ValidationIssue] = []
        apaar_id = str(record.get("apaar_id", "")).strip().replace(" ", "").replace("-", "")
        if not apaar_id or len(apaar_id) != 12:
            return issues

        # Check if student is actively enrolled at any OTHER AICTE institution
        clashing_records = context.db.query(Student).filter(
            Student.apaar_id == apaar_id,
            Student.institution_id != context.institution_id,
            Student.verification_status != "DE_ENROLLED"
        ).all()

        for clash in clashing_records:
            clash_inst = clash.institution
            clash_inst_name = clash_inst.name if clash_inst else "Another Institution"
            clash_aicte_id = clash_inst.aicte_id if clash_inst else "AICTE ID Unknown"

            issues.append(ValidationIssue(
                rule_code="CROSS_INSTITUTION_DUPLICATE",
                severity=RuleSeverity.CRITICAL,
                field_name="apaar_id",
                student_apaar=apaar_id,
                message=(
                    f"CRITICAL SEAT CLASH: Student APAAR {apaar_id} is actively registered as a full-time "
                    f"student at '{clash_inst_name}' (AICTE ID: {clash_aicte_id}) in {clash.program} ({clash.branch}). "
                    f"Dual enrolment in two simultaneous full-time technical programs violates AICTE Regulation 2026."
                ),
                fix_suggestion=(
                    "Verify student's official Migration / Transfer Certificate (TC). "
                    "An automated resolution case with SLA deadline has been initiated."
                )
            ))

        return issues
