from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from sqlalchemy.orm import Session

class RuleSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

@dataclass
class ValidationIssue:
    rule_code: str
    severity: RuleSeverity
    field_name: Optional[str]
    student_apaar: Optional[str]
    message: str
    fix_suggestion: Optional[str] = None
    row_index: Optional[int] = None
    auto_fixable: bool = False
    fixed_value: Optional[Any] = None

@dataclass
class ValidationContext:
    db: Session
    institution_id: str
    institution_name: str
    approved_intake: int
    current_enrolment: int
    batch_apaar_tracker: Set[str]  # In-batch duplicate tracker
    branch_intake_map: Dict[str, Dict[str, int]]  # branch_name -> {approved, current}
    academic_year: str = "2025-2026"

class BaseValidationRule(ABC):
    rule_code: str = "BASE_RULE"
    rule_name: str = "Base Validation Rule"
    severity: RuleSeverity = RuleSeverity.HIGH

    @abstractmethod
    def validate(self, record: Dict[str, Any], context: ValidationContext) -> List[ValidationIssue]:
        """Executes rule against record and context, returning any validation issues found."""
        pass
