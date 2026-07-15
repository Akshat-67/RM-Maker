from typing import List, Dict, Any
from .base import BaseValidator
from .models import Discrepancy, FixAction

class GenderValidator(BaseValidator):
    def supports(self, doc_type: str) -> bool:
        return doc_type == "RM"
        
    def validate(self, case_data: Dict[str, Any]) -> List[Discrepancy]:
        findings = []
        for idx, b in enumerate(case_data.get("bs", [])):
            if not isinstance(b, dict): continue
            sal = str(b.get("s", "")).strip().casefold()
            rel = str(b.get("r", "")).strip().casefold()
            gender = str(b.get("gender", "")).strip().casefold()
            
            path_prefix = f"bs.{idx}"
            
            # W/o means female/Mrs./Ms.
            if rel == "w/o" and (sal == "mr." or gender == "male"):
                findings.append(
                    Discrepancy(
                        category="gender",
                        severity="high",
                        explanation=f"Borrower {idx + 1} relation is 'W/o' but salutation is 'Mr.' or gender is 'Male'.",
                        suggested_fix="Change Salutation to Mrs./Ms. and Gender to Female.",
                        auto_fix_available=True,
                        auto_fix_payload=FixAction("replace", f"{path_prefix}.s", "Mrs.", "Change to Mrs."),
                        source_references=[
                            {"path": f"{path_prefix}.s", "value": b.get("s")},
                            {"path": f"{path_prefix}.r", "value": b.get("r")},
                            {"path": f"{path_prefix}.gender", "value": b.get("gender")}
                        ]
                    )
                )
            
            # S/o means male/Mr.
            if rel == "s/o" and (sal in ["mrs.", "ms."] or gender == "female"):
                findings.append(
                    Discrepancy(
                        category="gender",
                        severity="high",
                        explanation=f"Borrower {idx + 1} relation is 'S/o' but salutation is 'Mrs./Ms.' or gender is 'Female'.",
                        suggested_fix="Change Salutation to Mr. and Gender to Male.",
                        auto_fix_available=True,
                        auto_fix_payload=FixAction("replace", f"{path_prefix}.s", "Mr.", "Change to Mr."),
                        source_references=[
                            {"path": f"{path_prefix}.s", "value": b.get("s")},
                            {"path": f"{path_prefix}.r", "value": b.get("r")},
                            {"path": f"{path_prefix}.gender", "value": b.get("gender")}
                        ]
                    )
                )
                
            # Salutation Mrs./Ms. means Female
            if sal in ["mrs.", "ms."] and gender == "male":
                findings.append(
                    Discrepancy(
                        category="gender",
                        severity="medium",
                        explanation=f"Borrower {idx + 1} salutation is Mrs./Ms. but gender is Male.",
                        suggested_fix="Change Gender to Female.",
                        auto_fix_available=True,
                        auto_fix_payload=FixAction("replace", f"{path_prefix}.gender", "Female", "Change to Female"),
                        source_references=[
                            {"path": f"{path_prefix}.s", "value": b.get("s")},
                            {"path": f"{path_prefix}.gender", "value": b.get("gender")}
                        ]
                    )
                )
                
            # Salutation Mr. means Male
            if sal == "mr." and gender == "female":
                findings.append(
                    Discrepancy(
                        category="gender",
                        severity="medium",
                        explanation=f"Borrower {idx + 1} salutation is Mr. but gender is Female.",
                        suggested_fix="Change Gender to Male.",
                        auto_fix_available=True,
                        auto_fix_payload=FixAction("replace", f"{path_prefix}.gender", "Male", "Change to Male"),
                        source_references=[
                            {"path": f"{path_prefix}.s", "value": b.get("s")},
                            {"path": f"{path_prefix}.gender", "value": b.get("gender")}
                        ]
                    )
                )
        return findings
