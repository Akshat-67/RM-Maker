import re
from typing import List, Dict, Any
from .base import BaseValidator
from .models import Discrepancy

# Verhoeff tables for Aadhaar checksum validation
VERHOEFF_D = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 2, 3, 4, 0, 6, 7, 8, 9, 5],
    [2, 3, 4, 0, 1, 7, 8, 9, 5, 6],
    [3, 4, 0, 1, 2, 8, 9, 5, 6, 7],
    [4, 0, 1, 2, 3, 9, 5, 6, 7, 8],
    [5, 9, 8, 7, 6, 0, 4, 3, 2, 1],
    [6, 5, 9, 8, 7, 1, 0, 4, 3, 2],
    [7, 6, 5, 9, 8, 2, 1, 0, 4, 3],
    [8, 7, 6, 5, 9, 3, 2, 1, 0, 4],
    [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]
]

VERHOEFF_P = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 5, 7, 6, 2, 8, 3, 0, 9, 4],
    [5, 8, 0, 3, 7, 9, 6, 1, 4, 2],
    [8, 9, 1, 6, 0, 4, 3, 5, 2, 7],
    [9, 4, 5, 3, 1, 2, 6, 8, 7, 0],
    [4, 2, 8, 6, 5, 7, 3, 9, 0, 1],
    [2, 7, 9, 3, 8, 0, 6, 4, 1, 5],
    [7, 0, 4, 6, 9, 1, 3, 2, 5, 8]
]

VERHOEFF_INV = [0, 4, 3, 2, 1, 5, 6, 7, 8, 9]

def verhoeff_validate(number: str) -> bool:
    try:
        digits = [int(char) for char in number if char.isdigit()]
        if not digits:
            return False
        # Aadhaar numbers must be exactly 12 digits
        if len(digits) != 12:
            return False
        c = 0
        for i, item in enumerate(reversed(digits)):
            c = VERHOEFF_D[c][VERHOEFF_P[i % 8][item]]
        return c == 0
    except Exception:
        return False

class IdentityValidator(BaseValidator):
    def supports(self, doc_type: str) -> bool:
        return True  # Identity is validated for all deed types (RM, SD...)

    def validate(self, case_data: Dict[str, Any]) -> List[Discrepancy]:
        discrepancies = []
        
        # Collect all parties: format (path_prefix, index, dict_obj, display_name)
        parties = []
        
        # Determine labels dynamically based on document type
        doc_type = case_data.get("doc_type", "RM")
        is_sd = (doc_type == "SD" or "ss" in case_data)
        bs_label = "Buyer" if is_sd else "Borrower"
        
        # Borrowers / Buyers (key bs)
        for idx, p in enumerate(case_data.get("bs", [])):
            if isinstance(p, dict):
                parties.append(("bs", idx, p, f"{bs_label} {idx + 1}"))
                
        # Sellers (key ss - only in SD)
        for idx, p in enumerate(case_data.get("ss", [])):
            if isinstance(p, dict):
                parties.append(("ss", idx, p, f"Seller {idx + 1}"))
                
        # Witnesses (key ws)
        for idx, p in enumerate(case_data.get("ws", [])):
            if isinstance(p, dict):
                parties.append(("ws", idx, p, f"Witness {idx + 1}"))
                
        # Bank Signatory (key bsign - object, not list)
        bsign = case_data.get("bsign")
        if isinstance(bsign, dict) and bsign:
            parties.append(("bsign", None, bsign, "Bank Signatory"))

        # In-memory maps to identify duplicates
        aadhaar_map = {} # clean_id -> list of (party_label, path, raw_val)
        pan_map = {}     # pan_val -> list of (party_label, path, raw_val)

        for path_prefix, idx, p, label in parties:
            # 1. Aadhaar ID Check
            id_val = str(p.get("id", "")).strip()
            if id_val:
                # Remove spaces/dashes to get raw digits
                clean_id = "".join(char for char in id_val if char.isdigit())
                
                path = f"{path_prefix}.{idx}.id" if idx is not None else f"{path_prefix}.id"
                
                # Check format
                if len(clean_id) != 12:
                    discrepancies.append(
                        Discrepancy(
                            category="identity",
                            severity="high",
                            explanation=f"{label} Aadhaar number must be exactly 12 digits. Found: '{id_val}'",
                            suggested_fix="Correct the ID field to exactly 12 digits.",
                            source_references=[{"path": path, "value": id_val}]
                        )
                    )
                else:
                    # Checksum check
                    if not verhoeff_validate(clean_id):
                        discrepancies.append(
                            Discrepancy(
                                category="identity",
                                severity="high",
                                explanation=f"{label} Aadhaar checksum validation failed for value: '{id_val}'",
                                suggested_fix="Ensure the Aadhaar number is typed correctly.",
                                source_references=[{"path": path, "value": id_val}]
                            )
                        )
                
                if clean_id:
                    aadhaar_map.setdefault(clean_id, []).append((label, path, id_val))

            # 2. PAN Check
            pan_val = str(p.get("pan", "")).strip().upper()
            if pan_val:
                path = f"{path_prefix}.{idx}.pan" if idx is not None else f"{path_prefix}.pan"
                
                # Regex format check
                if not re.match(r"^[A-Z]{5}[0-9]{4}[A-Z]$", pan_val):
                    discrepancies.append(
                        Discrepancy(
                            category="identity",
                            severity="high",
                            explanation=f"{label} PAN number format invalid. Expected 10-char alphanumeric (e.g. ABCDE1234F). Found: '{pan_val}'",
                            suggested_fix="Correct the PAN format (5 letters, 4 digits, 1 letter).",
                            source_references=[{"path": path, "value": pan_val}]
                        )
                    )
                
                pan_map.setdefault(pan_val, []).append((label, path, pan_val))

        # Check duplicates
        for clean_id, list_of_parties in aadhaar_map.items():
            if len(list_of_parties) > 1:
                labels = [item[0] for item in list_of_parties]
                paths = [item[1] for item in list_of_parties]
                raw_val = list_of_parties[0][2]
                discrepancies.append(
                    Discrepancy(
                        category="identity",
                        severity="high",
                        explanation=f"Duplicate Aadhaar number '{raw_val}' shared by: {', '.join(labels)}.",
                        suggested_fix="Check documents and enter unique Aadhaar numbers.",
                        source_references=[{"path": p, "value": raw_val} for p in paths]
                    )
                )

        for pan_val, list_of_parties in pan_map.items():
            if len(list_of_parties) > 1:
                labels = [item[0] for item in list_of_parties]
                paths = [item[1] for item in list_of_parties]
                raw_val = list_of_parties[0][2]
                discrepancies.append(
                    Discrepancy(
                        category="identity",
                        severity="high",
                        explanation=f"Duplicate PAN number '{raw_val}' shared by: {', '.join(labels)}.",
                        suggested_fix="Check documents and enter unique PAN numbers.",
                        source_references=[{"path": p, "value": raw_val} for p in paths]
                    )
                )

        return discrepancies
