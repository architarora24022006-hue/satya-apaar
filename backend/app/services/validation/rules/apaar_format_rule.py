import re
from typing import Any, Dict, List
from app.services.validation.base_rule import BaseValidationRule, RuleSeverity, ValidationContext, ValidationIssue
from app.services.apaar_service import ApaarService

class ApaarFormatRule(BaseValidationRule):
    rule_code = "APAAR_FORMAT_CHECKSUM"
    rule_name = "12-Digit APAAR Format & Verhoeff Checksum Rule"
    severity = RuleSeverity.CRITICAL

    def validate(self, record: Dict[str, Any], context: ValidationContext) -> List[ValidationIssue]:
        issues: List[ValidationIssue] = []
        raw_apaar = str(record.get("apaar_id", "")).strip()

        if not raw_apaar:
            issues.append(ValidationIssue(
                rule_code="APAAR_MISSING",
                severity=RuleSeverity.CRITICAL,
                field_name="apaar_id",
                student_apaar=None,
                message="APAAR ID is missing or empty. Every AICTE student record must have a 12-digit APAAR ID.",
                fix_suggestion="Obtain candidate's 12-digit APAAR ID from ABC (Academic Bank of Credits) or DigiLocker."
            ))
            return issues

        # Check if formatting has spaces or hyphens that can be auto-cleaned
        cleaned_apaar = re.sub(r"[\s\-]", "", raw_apaar)
        if cleaned_apaar != raw_apaar and len(cleaned_apaar) == 12:
            issues.append(ValidationIssue(
                rule_code="APAAR_FORMAT_CLEANED",
                severity=RuleSeverity.INFO,
                field_name="apaar_id",
                student_apaar=cleaned_apaar,
                message=f"APAAR ID contained formatting characters ('{raw_apaar}'). Stripped to canonical 12 digits.",
                fix_suggestion="Auto-format to 12 contiguous numeric digits.",
                auto_fixable=True,
                fixed_value=cleaned_apaar
            ))

        # Check exact 12-digit length
        if len(cleaned_apaar) != 12 or not cleaned_apaar.isdigit():
            issues.append(ValidationIssue(
                rule_code="APAAR_INVALID_LENGTH",
                severity=RuleSeverity.CRITICAL,
                field_name="apaar_id",
                student_apaar=cleaned_apaar,
                message=f"Invalid APAAR length: Found {len(cleaned_apaar)} characters ('{cleaned_apaar}'). Must be exactly 12 numeric digits.",
                fix_suggestion="Verify the 12-digit number against the student's APAAR card."
            ))
            return issues

        # Check Verhoeff Checksum
        is_valid_checksum, error_msg = ApaarService.validate_format_and_checksum(cleaned_apaar)
        if not is_valid_checksum:
            issues.append(ValidationIssue(
                rule_code="APAAR_CHECKSUM_FAILED",
                severity=RuleSeverity.HIGH,
                field_name="apaar_id",
                student_apaar=cleaned_apaar,
                message=f"Verhoeff checksum verification failed for APAAR ID {cleaned_apaar}. Check digit mismatch.",
                fix_suggestion="Confirm student has not mistyped the last check digit of their APAAR ID."
            ))

        return issues
