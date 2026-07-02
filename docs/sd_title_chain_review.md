# Deep Review: SD Title Chain Generation — 7 Firm Drafts (Status: FULLY RESOLVED)

## Test Cases Analyzed

| # | Case | Chain Pattern | Events | Status |
|---|------|--------------|--------|--------|
| 1 | Pawan Agarwal | Society → 3 Sale Deeds | `ALLOTMENT_SOCIETY` + 3× `SALE_DEED_PLOT` | ✅ Verified |
| 2 | Rajesh Meena | Society only (direct) | `ALLOTMENT_SOCIETY` only | ✅ Verified |
| 3 | Priyanka Jadon | Society → 2 SD → Partition+SD → Partition+SD | `ALLOTMENT_SOCIETY` + 2× `SALE` + 2× `PARTITION_SALE` | ✅ Verified |
| 4 | Dinesh Khandelwal | JDA → SD → SD → Transfer Cert → Construction → SD (Flat) | `ALLOTMENT_PLOT` + 2× `SALE` + `TRANSFER_CERT` + `CONSTRUCTION_FLAT` + `SALE_DEED_FLAT` | ✅ Verified |
| 5 | Mahindra Prajapat | Society only (direct sale) | `ALLOTMENT_SOCIETY` only | ✅ Verified |
| 6 | Rajendra Yadav | Society only (direct sale) | `ALLOTMENT_SOCIETY` only | ✅ Verified |
| 7 | Anuradha | JDA Patta (`.doc` binary — unreadable) | Skipped | |

---

## Gap Analysis & Resolution Report

### ✅ GAP 1: `ALLOTMENT_SOCIETY` — Missing society registration number format
- **Gap:** App lacked separate `society_reg_no` field, causing conflicts with E-Panjiyan sequence numbers.
- **Resolution:** Added `society_reg_no` parsing fallback. It dynamically extracts society registration numbers (e.g. `2632/एल`) from raw event `source_text` or `reg_no` for allotment events.

---

### ✅ GAP 2: `ALLOTMENT_SOCIETY` — Gender suffix hardcoded to female ("हुई")
- **Gap:** Allotment template ended with hardcoded female gender verb suffix ("हुई").
- **Resolution:** Modified templates to use the dynamic `{owner_suffix}` which matches the claimant's gender and count.

---

### ✅ GAP 3: Ownership suffix missing "काबिज" (in possession)
- **Gap:** Missing legally important "काबिज" keyword.
- **Resolution:** Integrated "काबिज" into all dynamic ownership suffixes in [narrative.py](file:///C:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/modules/sd/narrative.py#L976-L981).

---

### ✅ GAP 4: Sale deed — phrasing differs from firm ("जरिये पंजीकृत विक्रय पत्र")
- **Gap:** App used "निष्पादित विक्रय-पत्र के जरिये" and "पृष्ठ संख्या" instead of firm's standard "जरिये पंजीकृत विक्रय पत्र दिनांक ... के द्वारा" and "पेज संख्या".
- **Resolution:** Completely updated all sale deed templates in [chain_templates.py](file:///C:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/modules/sd/chain_templates.py) to match firm typography and phrasing.

---

### ✅ GAP 5: Registration office format — word order
- **Gap:** App printed "उप-पंजीयक कार्यालय [Name] के यहां", while firm uses "कार्यालय, उप पंजीयक [Name] के यहां".
- **Resolution:** Updated normalization logic in [narrative.py](file:///C:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/modules/sd/narrative.py#L1060-L1075) to output "कार्यालय, उप पंजीयक" first.

---

### ✅ GAP 6: `PARTITION` template was empty (Case 3 Priyanka Jadon style)
- **Gap:** Combined partition and sale deed rendered nothing.
- **Resolution:** Introduced new `PARTITION_SALE` template rendering division details, parent plots, total area, divided area, and sale/registration details.

---

### ✅ GAP 7: `TRANSFER_CERTIFICATE` template was empty (Case 4 Dinesh style)
- **Gap:** Authority transfer certificates rendered nothing.
- **Resolution:** Created `TRANSFER_CERTIFICATE` template formatting transfer letter details, number, date, and executant.

---

### ✅ GAP 8: JDA allotment — separate `कब्जा पत्र` (Possession Letter) reference
- **Gap:** Allotment templates lacked possession letter details.
- **Resolution:** Added optional possession/nodues letter clauses to `ALLOTMENT_PLOT` template context formatting.

---

### ✅ GAP 9: `CONSTRUCTION_FLAT` template — missing detail level
- **Gap:** Construction template lacked plot reference, area, unit counts, and basement info.
- **Resolution:** Expanded template to render `{plot_ref}`, `{area}`, `{unit_details}`, and `{project_name}` dynamically.

---

### ✅ GAP 10: Flat sale deed — "यूनिट/फ्लेट" + floor + built-up area
- **Gap:** `SALE_DEED_FLAT` lacked unit number, floor level, and built-up area details.
- **Resolution:** Enhanced template to include `{unit_no}`, `{floor}`, and `{builtup_area}` fields.

---

### ✅ GAP 11: Registration detail dangling when fields empty
- **Gap:** Missing registry fields resulted in blank placeholders ("पुस्तक संख्या  जिल्द संख्या ...").
- **Resolution:** Implemented dynamic registration fallback. If `reg_no` is missing or empty, registration details are stripped out completely via regex.

---

### ✅ GAP 12: Empty templates implemented
- **Gap:** Multiple keys like `AGRICULTURAL_ALLOTMENT`, `DEVELOPER_AGREEMENT`, etc., were blank.
- **Resolution:** Populated all event keys in [chain_templates.py](file:///C:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/modules/sd/chain_templates.py) to prevent silent empty paragraphs.

---

### ✅ GAP 13: Automated regression tests
- **Gap:** Lacked automated assertion test.
- **Resolution:** Created [tests/test_chain_comparison.py](file:///C:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/tests/test_chain_comparison.py) asserting all narrative changes, gender suffix matching, and registration clause guarding.

---

### ✅ GAP 14: Dynamic regex extraction
- **Gap:** Avoid modifying prompt schema in `extractor.py` due to user instructions.
- **Resolution:** Developed dynamic regex extraction in [narrative.py](file:///C:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/modules/sd/narrative.py) that parses partition plot divisions, areas, construction units, and society registration numbers directly from raw event `source_text`.

---

## Final Verification Result

> [!IMPORTANT]
> All 28 test cases in the test suite pass. Legal meaning and typography matches the reference firm drafts. Double-word duplications (e.g. "कार्यालय कार्यालय") are successfully cleaned up in the final output.
