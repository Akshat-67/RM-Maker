from typing import List, Dict, Any
from .base import BaseValidator
from .models import Discrepancy

class MissingFieldsValidator(BaseValidator):
    def supports(self, doc_type: str) -> bool:
        return doc_type == "RM"
        
    def validate(self, case_data: Dict[str, Any]) -> List[Discrepancy]:
        findings = []
        
        # 1. Check execution date
        rd = str(case_data.get("rd", "")).strip()
        if not rd:
            findings.append(
                Discrepancy(
                    category="missing",
                    severity="high",
                    explanation="Deed Execution Date is missing.",
                    suggested_fix="Select an execution date in the case details."
                )
            )
            
        # 2. Check bank signatory
        bsign = case_data.get("bsign", {})
        if not bsign or not isinstance(bsign, dict):
            findings.append(
                Discrepancy(
                    category="missing",
                    severity="high",
                    explanation="Bank Signatory details are missing.",
                    suggested_fix="Configure Bank Signatory Name and Address."
                )
            )
        else:
            if not bsign.get("n"):
                findings.append(
                    Discrepancy(
                        category="missing",
                        severity="high",
                        explanation="Bank Signatory Name is missing.",
                        suggested_fix="Enter the bank signatory name.",
                        source_references=[{"path": "bsign.n", "value": ""}]
                    )
                )
            if not bsign.get("adr"):
                findings.append(
                    Discrepancy(
                        category="missing",
                        severity="medium",
                        explanation="Bank Signatory Address is missing.",
                        suggested_fix="Enter the bank signatory address.",
                        source_references=[{"path": "bsign.adr", "value": ""}]
                    )
                )
                
        # 3. Check borrowers
        borrowers = case_data.get("bs", [])
        if not borrowers:
             findings.append(
                Discrepancy(
                    category="missing",
                    severity="high",
                    explanation="No borrowers configured.",
                    suggested_fix="Add at least one borrower."
                )
            )
        else:
            for idx, b in enumerate(borrowers):
                if not isinstance(b, dict): continue
                path_prefix = f"bs.{idx}"
                name = str(b.get("n", "")).strip()
                id_val = str(b.get("id", "")).strip()
                pan = str(b.get("pan", "")).strip()
                adr = str(b.get("adr", "")).strip()
                rn = str(b.get("rn", "")).strip()
                
                if not name:
                    findings.append(
                        Discrepancy(
                            category="missing",
                            severity="high",
                            explanation=f"Borrower {idx + 1} Name is missing.",
                            suggested_fix="Enter borrower's full name.",
                            source_references=[{"path": f"{path_prefix}.n", "value": ""}]
                        )
                    )
                if not id_val:
                    findings.append(
                        Discrepancy(
                            category="missing",
                            severity="high",
                            explanation=f"Borrower {idx + 1} Aadhaar number is missing.",
                            suggested_fix="Enter the 12-digit Aadhaar number.",
                            source_references=[{"path": f"{path_prefix}.id", "value": ""}]
                        )
                    )
                if not pan:
                    findings.append(
                        Discrepancy(
                            category="missing",
                            severity="medium",
                            explanation=f"Borrower {idx + 1} PAN card is missing.",
                            suggested_fix="Enter the 10-digit PAN number.",
                            source_references=[{"path": f"{path_prefix}.pan", "value": ""}]
                        )
                    )
                if not adr:
                    findings.append(
                        Discrepancy(
                            category="missing",
                            severity="high",
                            explanation=f"Borrower {idx + 1} Address is missing.",
                            suggested_fix="Enter borrower's address.",
                            source_references=[{"path": f"{path_prefix}.adr", "value": ""}]
                        )
                    )
                if not rn:
                    findings.append(
                        Discrepancy(
                            category="missing",
                            severity="high",
                            explanation=f"Borrower {idx + 1} Relative Name is missing.",
                            suggested_fix="Enter father/husband relative name.",
                            source_references=[{"path": f"{path_prefix}.rn", "value": ""}]
                        )
                    )

        # 4. Check loans
        loans = case_data.get("ls", [])
        if not loans:
             findings.append(
                Discrepancy(
                    category="missing",
                    severity="high",
                    explanation="No loan entries configured.",
                    suggested_fix="Add at least one loan entry."
                )
            )
        else:
            for idx, l in enumerate(loans):
                if not isinstance(l, dict): continue
                path_prefix = f"ls.{idx}"
                amount = str(l.get("a", "")).strip()
                if not amount:
                    findings.append(
                        Discrepancy(
                            category="missing",
                            severity="high",
                            explanation=f"Loan {idx + 1} Amount is missing.",
                            suggested_fix="Enter the loan amount value.",
                            source_references=[{"path": f"{path_prefix}.a", "value": ""}]
                        )
                    )

        # 5. Check properties
        props = case_data.get("ps", [])
        if not props:
             findings.append(
                Discrepancy(
                    category="missing",
                    severity="high",
                    explanation="No property details configured.",
                    suggested_fix="Add at least one property description."
                )
            )
        else:
            for idx, p in enumerate(props):
                if not isinstance(p, dict): continue
                path_prefix = f"ps.{idx}"
                adr = str(p.get("adr", "")).strip()
                if not adr:
                    findings.append(
                        Discrepancy(
                            category="missing",
                            severity="high",
                            explanation=f"Property {idx + 1} Address is missing.",
                            suggested_fix="Enter the property address details.",
                            source_references=[{"path": f"{path_prefix}.adr", "value": ""}]
                        )
                    )
        
        return findings
