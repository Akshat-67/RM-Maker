# Hardcode Review Phase 2 - SD Replacements

This document audits the generic string replacements and normalizations currently residing in the codebase (specifically in `modules/sd/processor.py` and `utils/helpers.py`) to determine if they represent true normalization logic or hidden template/extraction compensation rules.

## Table of Classifications

| Rule / Snippet | Classification | Keep | Move | Remove |
| :--- | :--- | :--- | :--- | :--- |
| **Identity Boilerplate `(1).` -> `¼1½-`** | DEVLYS-NORMALIZATION | Keep | `utils/devlys_converter` | False |
| **Ligature `m[RrÙ]+jkf[/èk]+dkjh` -> `mÙkjkf/kdkjh`** | TEMPLATE-COMPENSATION | False | `templates/` | True |
| **DevLys Spelling `Iy‚V` -> `IykV`** | GENERIC BUT QUESTIONABLE | Keep | `utils/devlys_converter` | False |
| **Ligature `ç` -> `iz`** | DEVLYS-NORMALIZATION | Keep | `utils/devlys_converter` | False |
| **Template Spelling `Lo ` -> `Lo- `** | TEMPLATE-COMPENSATION | False | `templates/` | True |
| **Template Spelling `iêk` -> `iV~Vk`** | TEMPLATE-COMPENSATION | False | `templates/` | True |
| **Generic Punctuation `gSA, ]` -> `gS]`** | EXTRACTION-COMPENSATION | Keep | `processor` | False |
| **Regex Comma Removal `([A-Za-z]+), (iRuh)`** | EXTRACTION-COMPENSATION | Keep | `schema/extractor` | False |
| **Global Date Hyphen `(\d{2})&(\d{2})&(\d{4})`** | DEVLYS-NORMALIZATION | Keep | `utils/devlys_converter` | False |
| **Word-Perfect `Qlz~V` -> `QLVZ`** | TEMPLATE-COMPENSATION | False | `templates/` | True |
| **Surgical `è` ligatures `LoRo vf/kdkjksa` -> `LoRo vfèkdkjksa`** | TEMPLATE-COMPENSATION | False | `templates/` | True |
| **Paragraph 18 Alignment `ftu vf/kdkjksa...`** | TEMPLATE-COMPENSATION | False | `templates/` | True |
| **Smart Quotes `**` -> `@@TEMP_DBL_AST@@`** | DEVLYS-NORMALIZATION | Keep | `utils/devlys_converter` | False |
| **Helpers Pre-Map `निमर्ित` -> `निर्मित`** | EXTRACTION-COMPENSATION | Keep | `schema/extractor` | False |
| **Helpers Date Hyphens `(\d)\.(\d)` -> `\1-\2`** | GENERIC AND NECESSARY | Keep | `utils/helpers` | False |
| **Helpers Abbreviations `(\w)\.` -> `\1-`** | DEVLYS-NORMALIZATION | Keep | `utils/devlys_converter` | False |
| **Helpers Word Fix `ojxxt` -> `oxZxt`** | DEVLYS-NORMALIZATION | Keep | `utils/devlys_converter` | False |
| **Helpers Relation `स्वर्गीय` -> `स्व-`** | GENERIC BUT QUESTIONABLE | Keep | `utils/helpers` | False |

---

## Detailed Audit

### 1. Identity Boilerplate Fixes
**Snippet:**
```python
text = text.replace("(1).", "¼1½-")
```
**Why it exists:** Word processors often auto-format numbered lists into `(1).`. In DevLys, standard numbers and brackets have specific mappings. The generic DevLys converter likely struggles with the nested punctuation.
**Classification:** GENERIC AND NECESSARY (DevLys Normalization)
**Target Location:** Belong in the DevLys conversion module, not the rendering processor.

### 2. Ligature and Word-Perfect Fixes
**Snippet:**
```python
text = re.sub(r'm[RrÙ]+jkf[/èk]+dkjh', 'mÙkjkf/kdkjh', text)
text = text.replace("Qlz~V", "QLVZ").replace("vikj~VesUV", "vikVZesUV")
```
**Why it exists:** These are "Word-perfect mismatches" where the generated DevLys characters visually mean the same thing but have different underlying bytes than the template reference document.
**Classification:** TEMPLATE-COMPENSATION
**Target Location:** The `.docx` template should be updated to use the standard output of the DevLys engine rather than forcing the engine to output weird legacy spellings. SHOULD BE REMOVED.

### 3. Punctuation & Spacing Correction
**Snippet:**
```python
text = text.replace("gSA, ]", "gS]").replace("xokgku,", "xokgku~")
text = re.sub(r'([A-Za-z0-9&]+),\s*(iRuh|iq=|iq=h)', r'\1 \2', text)
```
**Why it exists:** The AI extractor sometimes outputs names with commas (e.g. `Pawan Kumar, S/O Daudayal`), which translates poorly. The AI also sometimes generates double punctuation at the end of sentences.
**Classification:** EXTRACTION-COMPENSATION
**Target Location:** The comma removal from relations should happen during extraction normalization/schema generation, not during rendering.

### 4. Surgical `è` ligatures
**Snippet:**
```python
text = text.replace("LoRo vf/kdkjksa", "LoRo vfèkdkjksa")
text = text.replace("ekfydkuk vf/kdkjksa", "ekfydkuk vfèkdkjksa")
```
**Why it exists:** The static Word template was typed by a human using the specific `è` ligature (Alt-code character) for the `/k` sound. The automated DevLys converter outputs standard `/k`.
**Classification:** TEMPLATE-COMPENSATION
**Target Location:** The Word template `.docx` must be updated to use standard `/k` so these surgical string matches are no longer needed. SHOULD BE REMOVED.

### 5. Paragraph 18 Parity Check
**Snippet:**
```python
text = text.replace("ftu vf/kdkjksa eq\"rdkZ vf/kdkjksa] lq[kkfèkdkjksa lfgr Ø; fd;k Fkk", "ftu vfèkdkjksa eq*rdkZ vfèkdkjksa] lq[kkf/kdkjksa lfgr Ø; fd;k Fkk")
```
**Why it exists:** A literal string match designed to perfectly recreate the spelling mistakes and specific mixed ligatures of Paragraph 18 in the source template to achieve zero parity diff.
**Classification:** TEMPLATE-COMPENSATION
**Target Location:** Update Paragraph 18 in the Word template. SHOULD BE REMOVED from the processor.

### 6. Helpers Pre-Mapping
**Snippet:**
```python
s = s.replace("निमर्ित", "निर्मित")
s = s.replace("स्वर्गीय", "स्व-").replace("स्व.", "स्व-")
```
**Why it exists:** The AI/OCR frequently misspells "निर्मित" or uses long-form relation strings ("स्वर्गीय").
**Classification:** EXTRACTION-COMPENSATION
**Target Location:** Should be handled in `schema.py` or the extractor normalization rules, rather than a global string replacement utility.

### 7. Helpers DevLys Spelling overrides
**Snippet:**
```python
res = res.replace("ojxxt", "oxZxt")
res = res.replace("ojxQhV", "oxZQhV")
```
**Why it exists:** The generic `Unicode_to_KrutiDev` engine fails to construct the complex "वर्गगज" (Sq Yards) DevLys string accurately, leading to "ojxxt".
**Classification:** DEVLYS-NORMALIZATION
**Target Location:** This belongs inside the core DevLys converter (`devlys_converter.py`), not inside a general "helpers" string mapping.
