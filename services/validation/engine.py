from typing import Dict, Any
from .registry import registry
from .models import ValidationResult

class ValidationEngine:
    @staticmethod
    def validate(doc_type: str, case_data: Dict[str, Any]) -> ValidationResult:
        all_discrepancies = []
        validators = registry.get_validators()
        
        for val in validators:
            if val.supports(doc_type):
                try:
                    findings = val.validate(case_data)
                    all_discrepancies.extend(findings)
                except Exception as e:
                    # If a validator fails, record a system discrepancy instead of crashing
                    from .models import Discrepancy
                    all_discrepancies.append(
                        Discrepancy(
                            category="system",
                            severity="high",
                            explanation=f"Validator {val.__class__.__name__} crash: {str(e)}",
                            suggested_fix="Check application logs."
                        )
                    )
        
        is_valid = not any(d.severity in ["high", "medium"] for d in all_discrepancies)
        return ValidationResult(is_valid=is_valid, discrepancies=all_discrepancies)
