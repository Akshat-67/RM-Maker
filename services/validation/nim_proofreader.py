import json
import logging
from openai import OpenAI
from utils.config import NVIDIA_NIM_API_KEY
from .models import Discrepancy

logger = logging.getLogger("NIMProofreader")

class NIMProofreader:
    @staticmethod
    def proofread(docx_text: str, session_data: dict, ocr_text: str = "", legal_text: str = "") -> list[Discrepancy]:
        if not NVIDIA_NIM_API_KEY:
            logger.warning("NVIDIA NIM API key missing, skipping proofreading.")
            return []
            
        try:
            client = OpenAI(
                base_url="https://integrate.api.nvidia.com/v1",
                api_key=NVIDIA_NIM_API_KEY
            )
            
            prompt = (
                "You are an expert legal proofreader. Compare the rendered Deed text against the official Ground Truth variables, the raw KYC document OCR text, and the Legal Search Report text.\n\n"
                "=== Ground Truth Variables (extracted/edited form data) ===\n"
                f"{json.dumps(session_data, indent=2, ensure_ascii=False)}\n\n"
                "=== Raw KYC Document OCR Text ===\n"
                f"{ocr_text}\n\n"
                "=== Legal Search Report Text ===\n"
                f"{legal_text}\n\n"
                "=== Rendered Deed Text ===\n"
                f"{docx_text}\n\n"
                "Identify any discrepancies between these four sources. Specifically, compare:\n"
                "1. The Gemini extracted borrower, banker, and witness values (Ground Truth Variables).\n"
                "2. The values filled in the actual Word draft (Rendered Deed Text).\n"
                "3. The values extracted from raw documents (Raw KYC Document OCR Text).\n"
                "4. The text of the Legal Scrutiny / Search Report (Legal Search Report Text).\n\n"
                "=== Core Rules to Keep in Mind ===\n"
                "1. Compare the borrower, banker, and witness(s) details across all three sources. This includes name, salutation, relative name, relation indicator (such as S/o, W/o, D/o, C/o), age, date of birth, address, Aadhaar number, and PAN number. Flag any mismatch or omission between what is in the raw scans, what is in the form variables, and what is written in the deed text.\n"
                "2. Compare the number of borrowers/owners mentioned in the Legal Search Report (under the Flow of Title / History of Title / Introduction sections) with the number of borrowers configured in the form variables (Ground Truth) and deed text (Rendered Deed Text). Flag a high severity error if they do not match.\n"
                "3. Verify that none of the witnesses listed in the deed draft (Rendered Deed Text / Ground Truth) are also the seller/present owner of the property as listed in the Legal Search Report (the current/present owner described as selling the property to the proposed buyers/borrowers). Flag a high severity error if a witness name matches the seller's name.\n"
                "4. Check for duplicate words or prefixes/suffixes (e.g., 'Mr. Mr.', 'Rupees Rupees', '/- /-', 'Only Only').\n"
                "5. Verify that critical sections or relative associations are not missing.\n"
                "6. Identify mismatched details (e.g., swapped details between borrowers).\n\n"
                "Return the results ONLY as a valid JSON list. Each object must have these exact keys:\n"
                "- 'category': 'proofreader'\n"
                "- 'severity': 'high', 'medium', or 'low'\n"
                "- 'explanation': '<description of discrepancy>'\n"
                "- 'suggested_fix': '<how to correct it>'\n"
                "Do NOT return any other text, markdown formatting, or explanations outside the JSON."
            )
            
            completion = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=4096,
                stream=False
            )
            
            content = completion.choices[0].message.content.strip()
            if content.startswith("```"):
                import re
                m = re.match(r"^```(?:json)?\s*(.*?)\s*```$", content, re.DOTALL | re.IGNORECASE)
                if m:
                    content = m.group(1).strip()
                    
            raw_findings = json.loads(content)
            findings = []
            for item in raw_findings:
                findings.append(
                    Discrepancy(
                        category=item.get("category", "proofreader"),
                        severity=item.get("severity", "medium"),
                        explanation=item.get("explanation", ""),
                        suggested_fix=item.get("suggested_fix", "")
                    )
                )
            return findings
            
        except Exception as e:
            logger.error(f"NIM Proofreader failed: {e}")
            return [
                Discrepancy(
                    category="proofreader",
                    severity="medium",
                    explanation=f"Secondary proofreader pass error: {str(e)}",
                    suggested_fix="Ensure NVIDIA_NIM_API_KEY is correct and NIM endpoint is reachable."
                )
            ]
