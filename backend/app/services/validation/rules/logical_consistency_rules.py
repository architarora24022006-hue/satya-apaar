from datetime import date, datetime
from typing import Any, Dict, List
from app.services.validation.base_rule import BaseValidationRule, RuleSeverity, ValidationContext, ValidationIssue

class LogicalConsistencyRule(BaseValidationRule):
    rule_code = "LOGICAL_CONSISTENCY"
    rule_name = "Logical Consistency & Policy Compliance Rule"
    severity = RuleSeverity.HIGH

    def parse_date(self, val: Any) -> Any:
        if isinstance(val, (date, datetime)):
            return val if isinstance(val, date) else val.date()
        if isinstance(val, str):
            for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"):
                try:
                    return datetime.strptime(val.strip(), fmt).date()
                except ValueError:
                    continue
        return None

    def validate(self, record: Dict[str, Any], context: ValidationContext) -> List[ValidationIssue]:
        issues: List[ValidationIssue] = []
        apaar_id = record.get("apaar_id")

        # 1. NRI + OCI / Foreign National Conflict
        is_nri = bool(record.get("is_nri", False))
        is_oci = bool(record.get("is_oci", False))
        is_fn = bool(record.get("is_foreign_national", False))

        if is_nri and is_fn:
            issues.append(ValidationIssue(
                rule_code="CONFLICT_NRI_FOREIGN_NATIONAL",
                severity=RuleSeverity.HIGH,
                field_name="quota_type",
                student_apaar=apaar_id,
                message="Logical conflict: Student cannot simultaneously hold Non-Resident Indian (NRI) and Foreign National (FN) quota.",
                fix_suggestion="Select either NRI status (Indian passport abroad) or Foreign National status."
            ))

        if is_nri and is_oci:
            issues.append(ValidationIssue(
                rule_code="CONFLICT_NRI_OCI",
                severity=RuleSeverity.WARNING,
                field_name="quota_type",
                student_apaar=apaar_id,
                message="Ambiguity: Overseas Citizen of India (OCI) cardholder marked under Non-Resident Indian (NRI) category.",
                fix_suggestion="Standardize to OCI category per AICTE Foreign Admissions Guidelines."
            ))

        # 2. Age Check (DOB vs Admission Date)
        dob = self.parse_date(record.get("dob"))
        adm_date = self.parse_date(record.get("admission_date"))

        if dob and adm_date:
            age_at_admission = (adm_date - dob).days / 365.25
            if age_at_admission < 15.0:
                issues.append(ValidationIssue(
                    rule_code="IMPOSSIBLE_AGE_UNDERAGE",
                    severity=RuleSeverity.HIGH,
                    field_name="dob",
                    student_apaar=apaar_id,
                    message=f"Impossible age: Student age at admission is {age_at_admission:.1f} years (DOB: {dob}). Minimum age for technical degree admission is 15.5 years.",
                    fix_suggestion="Verify Date of Birth on 10th Standard / Matriculation Certificate."
                ))
            elif age_at_admission > 60.0:
                issues.append(ValidationIssue(
                    rule_code="IMPOSSIBLE_AGE_OVERAGE",
                    severity=RuleSeverity.HIGH,
                    field_name="dob",
                    student_apaar=apaar_id,
                    message=f"Anomalous age: Student age at admission is {age_at_admission:.1f} years (DOB: {dob}). Exceeds typical student profile.",
                    fix_suggestion="Confirm Date of Birth against Aadhaar / APAAR record."
                ))

        # 3. Supernumerary without quota / category justification
        is_supernumerary = bool(record.get("is_supernumerary", False))
        quota = str(record.get("quota_type", "")).strip().title()
        category = str(record.get("category", "")).strip().upper()

        if is_supernumerary and quota not in ["Supernumerary", "Nri", "Tfw", "Ews", "Pmsss", "J&K"]:
            issues.append(ValidationIssue(
                rule_code="SUPERNUMERARY_WITHOUT_JUSTIFICATION",
                severity=RuleSeverity.HIGH,
                field_name="is_supernumerary",
                student_apaar=apaar_id,
                message="Supernumerary flag is set to TRUE, but quota type is marked as regular Merit/Management.",
                fix_suggestion="Specify authorized supernumerary category: TFW (Tuition Fee Waiver), PMSSS, EWS, or J&K quota."
            ))

        # 4. Admission Date outside the Academic Window
        if adm_date:
            # Academic admission window for 2025-26: June 1, 2025 to Oct 31, 2025
            window_start = date(2025, 6, 1)
            window_end = date(2025, 10, 31)
            if adm_date < window_start or adm_date > window_end:
                issues.append(ValidationIssue(
                    rule_code="ADMISSION_DATE_OUTSIDE_WINDOW",
                    severity=RuleSeverity.WARNING,
                    field_name="admission_date",
                    student_apaar=apaar_id,
                    message=f"Admission date '{adm_date}' falls outside the sanctioned AICTE 2025-2026 academic window (June 1 - October 31, 2025).",
                    fix_suggestion="Verify admission counselling allotment date or submit AICTE special extension notification."
                ))

        return issues
