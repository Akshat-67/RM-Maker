# Hardcode Decisions

This document converts the findings from the Phase 1 and Phase 2 codebase audits into formal project decisions regarding text replacement rules, hardcoded logic, and technical debt in the SD (Sale Deed) processing pipeline.

## 1. ACCEPTED

### Case-Specific Replacements Must Be Removed
**Decision:** Accepted.
Confirmed case-specific overfitting strings (e.g., Pawan Kumar, Plot A-23, Lease D-2341, Ganpatpura) violate the generalized nature of the drafting engine. These represent strict overfitting and have already been removed.

### DevLys Normalization Is A Valid Category
**Decision:** Accepted.
Standard character normalization, ligature alignment, numbering normalization, punctuation, and encoding normalization are valid requirements. The existence of these rules is acceptable, and they are not automatically considered harmful hardcodes.

### Extraction Compensation Exists
**Decision:** Accepted.
Rules that explicitly clean up OCR errors, trailing commas, or malformed extraction data are valid findings. Many of these issues conceptually belong earlier in the pipeline (e.g., extraction or schema) rather than at the rendering layer.

### Template Compensation Exists
**Decision:** Accepted.
The audit successfully demonstrated that some python string replacement rules exist solely to compensate for typos, formatting inconsistencies, or legacy DevLys spelling inconsistencies embedded directly in the `.docx` templates.

---

## 2. PARTIALLY ACCEPTED

### Move Normalization Upstream
**Decision:** Partially Accepted.
While the direction is reasonable, we do not assume every rule must immediately leave `processor.py`. Individual evaluation is required to determine if a rule legitimately belongs in rendering vs upstream layers.

### Move Rules Into DevLys Layer
**Decision:** Partially Accepted.
Some DevLys normalizations may eventually belong in `devlys_converter.py` or dedicated modules, but no decision has been made to radically reorganize the rendering pipeline yet.

### Extraction Compensation Relocation
**Decision:** Partially Accepted.
Relocating extraction compensation rules (to `extractor`, `schema`, or normalization) is valid in concept, but each rule must be individually evaluated before execution.

---

## 3. REJECTED

### Remove All Replacement Rules
**Decision:** Rejected.
The project rejects the assumption that all string replacements are bad. Many are legitimate rendering requirements, normalizations, and DevLys adaptations.

### Rewrite Rendering Pipeline
**Decision:** Rejected.
The audit does not provide sufficient evidence to justify a massive rewrite of the rendering layer at this time.

### Rewrite DevLys System
**Decision:** Rejected.
Not approved.

---

## 4. ON HOLD

### Template Compensation Removal
**Decision:** On Hold.
While the existence of template compensation is accepted, actually removing individual compensation rules requires a meticulous review of template content, template ownership, and parity impacts before any implementation is approved.

### Processor Cleanup
**Decision:** On Hold.
Large-scale structural cleanup of the processor requires broader architectural review.

---

## 5. Text Replacement Classification Matrix

| Rule | Classification | Keep | Move | Remove | Reason |
| ---- | -------------- | ---- | ---- | ------ | ------ |
| `(1).` -> `¼1½-` | DEVLYS_NORMALIZATION | Yes | No | No | Valid translation of English-style numbering into DevLys brackets. |
| `m[RrÙ]+jkf[/èk]+dkjh` -> `mÙkjkf/kdkjh` | TEMPLATE_COMPENSATION | Yes | No | No (On Hold) | Fixing visual parity mismatch driven by template legacy spelling. |
| `Iy‚V` -> `IykV` | DEVLYS_NORMALIZATION | Yes | No | No | Valid DevLys spelling override for 'Plot'. |
| `ç` -> `iz` | DEVLYS_NORMALIZATION | Yes | No | No | Valid ligature normalization. |
| `Lo ` -> `Lo- ` | TEMPLATE_COMPENSATION | Yes | No | No (On Hold) | Forcing template spacing rules over the generated output. |
| `iêk` -> `iV~Vk` | TEMPLATE_COMPENSATION | Yes | No | No (On Hold) | Fixing visual parity mismatch driven by template legacy spelling. |
| `gSA, ]` -> `gS]` | EXTRACTION_COMPENSATION | Yes | No | No | AI occasionally hallucinates double punctuation at sentence ends. |
| `([A-Za-z]+), (iRuh)` | EXTRACTION_COMPENSATION | Yes | No | No | Removes AI-generated commas between names and relations. |
| `(\d{2})&(\d{2})&(\d{4})` | DEVLYS_NORMALIZATION | Yes | No | No | Global date hyphen parsing rule for DevLys. |
| `Qlz~V` -> `QLVZ` | TEMPLATE_COMPENSATION | Yes | No | No (On Hold) | Word-perfect ligature fix compensating for template spelling. |
| `LoRo vf/kdkjksa` -> `LoRo vfèkdkjksa` | TEMPLATE_COMPENSATION | Yes | No | No (On Hold) | Surgical ligature fix (`è` vs `/k`) compensating for static template. |
| `ftu vf/kdkjksa eq\"rdkZ...` | TEMPLATE_COMPENSATION | Yes | No | No (On Hold) | Literal match for Paragraph 18 to recreate template typos/parity. |
| `**` -> `@@TEMP_DBL_AST@@` | DEVLYS_NORMALIZATION | Yes | No | No | Valid DevLys smart quote translation protection. |
| `निमर्ित` -> `निर्मित` | EXTRACTION_COMPENSATION | Yes | No | No | Frequent OCR/AI hallucination fix in pre-mapping. |
| `(\d)\.(\d)` -> `\1-\2` | DEVLYS_NORMALIZATION | Yes | No | No | Handles decimal dates/numbers properly before mapping. |
| `ojxxt` -> `oxZxt` | DEVLYS_NORMALIZATION | Yes | No | No | DevLys construction workaround for "वर्गगज". |
| `स्वर्गीय` -> `स्व-` | EXTRACTION_COMPENSATION | Yes | No | No | Standardizing relations extracted by the AI in long-form. |

*(Note: "Move" and "Remove" for Template/Extraction items are marked 'No' or 'On Hold' per the current architectural decisions. They will remain in place until specific removal execution phases are approved.)*

---

## 6. Future Cleanup Order

When addressing remaining technical debt, the order of operations should be prioritized by risk:

**1. Safest to Clean (Low Risk)**
*   **Extraction Compensations:** Standardizing relations (`स्वर्गीय`), fixing trailing commas, and correcting AI punctuation hallucinations (`gSA, ]`) are extremely safe to clean up. The fix merely requires moving the logic upstream into the `schema` validation or `extractor` classes, making the rendering processor cleaner.

**2. Medium Risk**
*   **Template Compensations:** Removing rules like surgical `è` ligatures or Word-perfect fixes (`Qlz~V` -> `QLVZ`) requires simultaneous modification of the underlying `.docx` templates across multiple directories. It is a synchronized two-step process that risks parity regressions if a template is missed.

**3. Highest Risk**
*   **DevLys Normalization Relocation:** Attempting to relocate or rewrite the DevLys regex rules (e.g., date hyphen parsing or `ç` -> `iz`) carries massive risk of breaking the entire Hindi font rendering system. This should be avoided unless a dedicated DevLys subsystem rewrite is approved.

---

## 7. Architectural Conclusions

The rendering layer (`modules/sd/processor.py`) is heavily populated with string replacements. However, the audit has proven that **not all replacements are bad**.

Many replacements are legitimate **DevLys Normalizations** ensuring output renders correctly in the legacy font. Others are **Extraction Compensations** covering for AI/OCR weaknesses, or **Template Compensations** fixing mismatched parity driven by static Word files.

While the ultimate goal might be a clean rendering processor, we explicitly reject a blanket rewrite. Future codebase evolution must target specific categories (like moving extraction compensation upstream) while leaving the complex, functioning DevLys normalizations intact.
