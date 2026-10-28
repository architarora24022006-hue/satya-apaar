from typing import Any, Dict, List
from app.services.validation.base_rule import BaseValidationRule, RuleSeverity, ValidationContext, ValidationIssue

class IntakeCapacityRule(BaseValidationRule):
    rule_code = "INTAKE_CAPACITY_RULE"
    rule_name = "Live Seat Lock & Sanctioned Intake Capacity Rule"
    severity = RuleSeverity.CRITICAL

    def validate(self, record: Dict[str, Any], context: ValidationContext) -> List[ValidationIssue]:
        issues: List[ValidationIssue] = []
        branch = str(record.get("branch", "")).strip()
        is_supernumerary = bool(record.get("is_supernumerary", False)) or str(record.get("quota_type", "")).lower() == "supernumerary"

        # Lookup branch capacity in context map
        branch_stats = context.branch_intake_map.get(branch)
        if not branch_stats:
            # Fallback to general institution level if specific branch not tracked
            approved = context.approved_intake
            current = context.current_enrolment
        else:
            approved = branch_stats.get("approved", 60)
            current = branch_stats.get("current", 0)

        projected = current + 1
        fill_ratio = (current / approved) if approved > 0 else 0.0

        if not is_supernumerary:
            # Normal admissions logic
            if current >= approved:
                issues.append(ValidationIssue(
                    rule_code="SEAT_LOCK_BREACH",
                    severity=RuleSeverity.CRITICAL,
                    field_name="branch",
                    student_apaar=record.get("apaar_id"),
                    message=(
                        f"AICTE LIVE SEAT LOCK ENGAGED: Branch '{branch}' has reached 100% sanctioned capacity "
                        f"({current}/{approved} seats). Regular admissions are blocked. "
                        f"Supernumerary admission requires formal justification and regulatory approval."
                    ),
                    fix_suggestion=(
                        "Submit a supernumerary exception request (PMSSS/EWS/TFW/J&K/NRI) with supporting council documentation "
                        "or reassign student to an under-capacity branch."
                    )
                ))
            elif fill_ratio >= 0.90:
                issues.append(ValidationIssue(
                    rule_code="SEAT_WARNING_90_PERCENT",
                    severity=RuleSeverity.WARNING,
                    field_name="branch",
                    student_apaar=record.get("apaar_id"),
                    message=(
                        f"SEAT ALLOCATION WARNING: Branch '{branch}' is at {round(fill_ratio * 100, 1)}% of sanctioned intake "
                        f"({current}/{approved} seats). Normal admissions will automatically lock once capacity is reached."
                    ),
                    fix_suggestion="Monitor remaining available seats closely before closing admissions."
                ))
        else:
            # Supernumerary quota admission logic (allowed up to 15% supernumerary ceiling)
            supernumerary_ceiling = int(approved * 0.15)
            # If current enrolled exceeds regular + supernumerary ceiling:
            if current >= (approved + supernumerary_ceiling):
                issues.append(ValidationIssue(
                    rule_code="SUPERNUMERARY_CEILING_EXCEEDED",
                    severity=RuleSeverity.CRITICAL,
                    field_name="quota_type",
                    student_apaar=record.get("apaar_id"),
                    message=(
                        f"SUPERNUMERARY INTAKE BREACH: Total admissions exceed regular intake ({approved}) "
                        f"and maximum permitted 15% supernumerary ceiling ({supernumerary_ceiling} seats)."
                    ),
                    fix_suggestion="Obtain special AICTE Executive Council dispensation."
                ))

        # Increment tracker in context for subsequent batch rows
        if branch_stats:
            branch_stats["current"] = projected
        context.current_enrolment += 1

        return issues
