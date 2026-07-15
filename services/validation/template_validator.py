import re
from typing import List, Dict, Any
from .base import BaseValidator
from .models import Discrepancy

class TemplateValidator(BaseValidator):
    def supports(self, doc_type: str) -> bool:
        return doc_type == "RM"
        
    def validate(self, case_data: Dict[str, Any]) -> List[Discrepancy]:
        findings = []
        selected_template = str(case_data.get("selected_template", "")).strip()
        if not selected_template:
            return findings
            
        # Extract borrowers and loans counts from selected template filename (e.g. RM_ICICI_2B_1L)
        b_match = re.search(r'(\d+)b', selected_template, re.IGNORECASE)
        l_match = re.search(r'(\d+)l', selected_template, re.IGNORECASE)
        
        borrowers = case_data.get("bs", [])
        # Count non-empty borrowers
        b_count_active = sum(1 for b in borrowers if isinstance(b, dict) and b.get("n"))
        
        loans = case_data.get("ls", [])
        # Count non-empty loans
        l_count_active = sum(1 for l in loans if isinstance(l, dict) and l.get("a"))
        
        if b_match:
            template_b_count = int(b_match.group(1))
            if b_count_active != template_b_count:
                findings.append(
                    Discrepancy(
                        category="template",
                        severity="high",
                        explanation=f"Selected template '{selected_template}' is configured for {template_b_count} Borrower(s), but you have {b_count_active} active Borrower(s) configured.",
                        suggested_fix="Select a template matching your borrower count, or adjust your borrower configurations."
                    )
                )
                
        if l_match:
            template_l_count = int(l_match.group(1))
            if l_count_active != template_l_count:
                findings.append(
                    Discrepancy(
                        category="template",
                        severity="high",
                        explanation=f"Selected template '{selected_template}' is configured for {template_l_count} Loan(s), but you have {l_count_active} active Loan(s) configured.",
                        suggested_fix="Select a template matching your loan count."
                    )
                )
                
        # Also check bank template mismatch
        bank = str(case_data.get("bank", "")).strip().upper()
        if bank and bank not in selected_template.upper() and not selected_template.startswith("custom_"):
            findings.append(
                Discrepancy(
                    category="template",
                    severity="medium",
                    explanation=f"Selected template '{selected_template}' does not appear to match the active Bank selection '{bank}'.",
                    suggested_fix="Ensure you have selected the correct bank template."
                )
            )
            
        return findings
