from typing import List, Dict, Any, Optional

class FixAction:
    def __init__(self, action_type: str, target_path: str, value: Any, label: str):
        self.action_type = action_type  # e.g., "replace"
        self.target_path = target_path  # e.g., "bs.0.id"
        self.value = value
        self.label = label

    def to_dict(self) -> dict:
        return {
            "action_type": self.action_type,
            "target_path": self.target_path,
            "value": self.value,
            "label": self.label
        }

class Discrepancy:
    def __init__(
        self,
        category: str,
        severity: str,
        explanation: str,
        suggested_fix: str,
        auto_fix_available: bool = False,
        auto_fix_payload: Optional[FixAction] = None,
        source_references: Optional[List[dict]] = None
    ):
        self.category = category
        self.severity = severity  # "high", "medium", "low"
        self.explanation = explanation
        self.suggested_fix = suggested_fix
        self.auto_fix_available = auto_fix_available
        self.auto_fix_payload = auto_fix_payload
        self.source_references = source_references or []

    def to_dict(self) -> dict:
        return {
            "category": self.category,
            "severity": self.severity,
            "explanation": self.explanation,
            "suggested_fix": self.suggested_fix,
            "auto_fix_available": self.auto_fix_available,
            "auto_fix_payload": self.auto_fix_payload.to_dict() if self.auto_fix_payload else None,
            "source_references": self.source_references
        }

class ValidationResult:
    def __init__(self, is_valid: bool, discrepancies: List[Discrepancy]):
        self.is_valid = is_valid
        self.discrepancies = discrepancies

    def to_dict(self) -> dict:
        return {
            "is_valid": self.is_valid,
            "discrepancies": [d.to_dict() for d in self.discrepancies]
        }
