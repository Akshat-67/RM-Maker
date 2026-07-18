from typing import List, Dict, Any
from .base import BaseValidator
from .models import Discrepancy, FixAction

class ThreeWayValidator(BaseValidator):
    def supports(self, doc_type: str) -> bool:
        return doc_type in ["RM", "SD"]

    def validate(self, case_data: Dict[str, Any]) -> List[Discrepancy]:
        findings = []
        
        nvidia_data = case_data.get("nvidia_data", {})
        gemini_data = case_data.get("gemini_data", {})
        
        # Helper to compare values case-insensitively and strip whitespace
        def normalize(v):
            if v is None:
                return ""
            return str(v).strip().lower()

        # Helper to normalize numeric values (ignoring commas, decimals, trailing zeroes)
        def normalize_num(v):
            if v is None or v == "":
                return ""
            try:
                # Remove currency symbols and commas
                s = str(v).replace(",", "").replace("₹", "").strip()
                # Parse as float
                val = float(s)
                # If it's an integer value, format as integer string
                if val.is_integer():
                    return str(int(val))
                return f"{val:.2f}"
            except ValueError:
                return str(v).strip().lower()

        # ----------------------------------------------------
        # 1. Compare Borrowers (bs / ss / bs for SD)
        # ----------------------------------------------------
        # The key for borrowers is 'bs' in RM/SD (or sometimes 'ss', 'bs' in SD data)
        # Let's check both 'bs' and 'ss'/'bs'
        keys_to_check = []
        if case_data.get("doc_type") == "SD":
            keys_to_check = [("ss", "Seller"), ("bs", "Buyer"), ("ws", "Witness")]
        else:
            keys_to_check = [("bs", "Borrower"), ("ls", "Loan"), ("ws", "Witness")]

        for key, label in keys_to_check:
            current_list = case_data.get(key, [])
            nvidia_list = nvidia_data.get(key, [])
            gemini_list = gemini_data.get(key, [])

            if not isinstance(current_list, list):
                continue

            max_len = max(len(current_list), len(nvidia_list), len(gemini_list))
            for idx in range(max_len):
                curr_item = current_list[idx] if idx < len(current_list) else {}
                nv_item = nvidia_list[idx] if idx < len(nvidia_list) else {}
                gem_item = gemini_list[idx] if idx < len(gemini_list) else {}

                # Fields to verify depending on the category
                if key in ["bs", "ss", "bs"]:
                    fields = [
                        ("n", "Name", False),
                        ("aadh", "Aadhaar", True),
                        ("pan", "PAN", False),
                        ("r_n", "Relative Name", False),
                        ("r_rel", "Relationship", False),
                        ("adr", "Address", False)
                    ]
                elif key == "ls":
                    fields = [
                        ("amt", "Amount", True),
                        ("lan", "Loan Account Number", False),
                        ("ten", "Tenure", True),
                        ("int", "Interest Rate", True)
                    ]
                else: # ws
                    fields = [
                        ("n", "Name", False),
                        ("adr", "Address", False)
                    ]

                for field_key, field_name, is_numeric in fields:
                    curr_val = curr_item.get(field_key, "") if isinstance(curr_item, dict) else ""
                    nv_val = nv_item.get(field_key, "") if isinstance(nv_item, dict) else ""
                    gem_val = gem_item.get(field_key, "") if isinstance(gem_item, dict) else ""

                    # We skip comparison if both verifications are missing
                    if not nv_val and not gem_val:
                        continue

                    norm_curr = normalize_num(curr_val) if is_numeric else normalize(curr_val)
                    norm_nv = normalize_num(nv_val) if is_numeric else normalize(nv_val)
                    norm_gem = normalize_num(gem_val) if is_numeric else normalize(gem_val)

                    # A. Compare Form vs Gemini (If Gemini verification was run)
                    if gem_val and norm_curr != norm_gem:
                        findings.append(
                            Discrepancy(
                                category="verification",
                                severity="high" if field_key in ["aadh", "pan", "amt", "lan", "n"] else "medium",
                                explanation=f"{label} {idx + 1} {field_name} is '{curr_val or '(Empty)'}' but Gemini extracted '{gem_val}'.",
                                suggested_fix=f"Change {field_name.lower()} to '{gem_val}'.",
                                auto_fix_available=True,
                                auto_fix_payload=FixAction(
                                    action_type="replace",
                                    target_path=f"{key}.{idx}.{field_key}",
                                    value=gem_val,
                                    label=f"Use Gemini value ('{gem_val}')"
                                )
                            )
                        )

                    # B. Compare Form vs NVIDIA (If background extraction was run)
                    elif nv_val and norm_curr != norm_nv:
                        findings.append(
                            Discrepancy(
                                category="verification",
                                severity="high" if field_key in ["aadh", "pan", "amt", "lan", "n"] else "medium",
                                explanation=f"{label} {idx + 1} {field_name} is '{curr_val or '(Empty)'}' but NVIDIA pre-extracted '{nv_val}'.",
                                suggested_fix=f"Change {field_name.lower()} to '{nv_val}'.",
                                auto_fix_available=True,
                                auto_fix_payload=FixAction(
                                    action_type="replace",
                                    target_path=f"{key}.{idx}.{field_key}",
                                    value=nv_val,
                                    label=f"Use NVIDIA value ('{nv_val}')"
                                )
                            )
                        )

                    # C. Compare NVIDIA vs Gemini (Discrepancy between AIs)
                    if nv_val and gem_val and norm_nv != norm_gem:
                        findings.append(
                            Discrepancy(
                                category="verification",
                                severity="medium",
                                explanation=f"AI Discrepancy: For {label} {idx + 1} {field_name}, Gemini extracted '{gem_val}' but NVIDIA pre-extracted '{nv_val}'.",
                                suggested_fix="Manually check original scans to verify the correct spelling/value.",
                                auto_fix_available=False
                            )
                        )

        return findings
