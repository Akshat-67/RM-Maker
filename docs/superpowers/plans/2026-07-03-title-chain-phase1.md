# Title Chain Phase 1 Improvements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement Phase 1 improvements of the Title Chain feature to fix the manual override generation discard bug and sync property boundaries reactively.

**Architecture:** Add a whitelisted `chain_is_manual` flag to the session data. Use this flag in the Flask controller to bypass templated compilation of the title chain text during document generation, and add DOM change event listeners on property inputs in the frontend to trigger card narrative updates.

**Tech Stack:** Flask (Python 3.10+), Vanilla JS (ES6), HTML5/CSS3.

## Global Constraints

- DO NOT modify extraction prompts, merging logic, relation splitting, or normalization helpers in `modules/sd/extractor.py`, `modules/rm/extractor.py`, `modules/rm/schema.py`, or `utils/helpers.py`.
- Devanagari numerals (०-९) must always be converted to standard English digits (0-9) globally.
- The verification UI must present Hindi text in a clean Unicode Devanagari font (Segoe UI or Mangal). Legacy fonts (DevLys 010 / Kruti Dev) must never be used to style browser inputs.
- Protect automatic transliteration and clean typography UI workflows.
- Protect Registered Mortgage (RM) relation and UI workflows.

---

### Task 1: Schema Integration and Save Route Support

**Files:**
- Modify: `modules/sd/schema.py:37-44`
- Modify: `app.py:720-752`

**Interfaces:**
- Consumes: JSON save payload containing `chain_is_manual` flag
- Produces: Persistent `chain_is_manual` field inside `session["data"]` in `session.json`

- [ ] **Step 1: Modify modules/sd/schema.py to whitelist chain_is_manual**

Modify the `sd_keys` whitelist in `prune_sd_data(...)`:
```python
    sd_keys = [
        "rd", "amount", "amount_words", "consideration", "tds", "hypothecation", 
        "ss", "bs", "ps", "ws", "title_chain", "reg", "unassigned_aadhars", 
        "sellers", "buyers", "chain", "chain_text", "payments", "seller_label", 
        "buyer_label", "chain_is_manual"
    ]
```

- [ ] **Step 2: Update save_case route in app.py to preserve chain_is_manual flag**

Confirm `chain_is_manual` is correctly saved to session data in route `save_case(...)` inside `app.py`. Since it is whitelisted in `prune_sd_data(...)`, it will automatically be serialized in `session.json` under `data`.

- [ ] **Step 3: Verify schema loading/saving**

Create a temporary python script in `scratch/test_schema.py` to assert that `chain_is_manual` is not pruned.
```python
# scratch/test_schema.py
import sys
sys.path.append('.')
from modules.sd.schema import prune_sd_data

data = {"chain_text": "testing manual text", "chain_is_manual": "true"}
pruned = prune_sd_data(data)
assert pruned.get("chain_is_manual") == "true", "chain_is_manual was pruned!"
print("Schema verification passed!")
```
Run: `python scratch/test_schema.py`
Expected: Print "Schema verification passed!" without errors.

- [ ] **Step 4: Commit schema changes**

```bash
git add modules/sd/schema.py
git commit -m "feat: whitelist chain_is_manual in SD schema"
```

---

### Task 2: Backend Document Generation Manual Override Support

**Files:**
- Modify: `app.py:1467-1478`

**Interfaces:**
- Consumes: `context.get("chain_is_manual")` flag
- Produces: Paragraph splits `context["chain_paragraphs"]` generated directly from user's manual edits in `context["chain_text"]`

- [ ] **Step 1: Modify document generation route in app.py**

Modify the `/case/<case_id>/generate` endpoint in `app.py` to bypass `generate_chain_narrative` compilation if `chain_is_manual` evaluates to `"true"` or `True`:
```python
    # Now generate chain paragraphs since we have computed ps fields
    if doc_type == "SD":
        if context.get("chain_is_manual") in ["true", True]:
            # Bypass template compilation, respect user's manual edits
            if context.get("chain_text"):
                context["chain_paragraphs"] = [p.strip() for p in context["chain_text"].split("\n\n") if p.strip()]
            else:
                context["chain_paragraphs"] = []
        elif "title_chain" in context and isinstance(context["title_chain"], list) and len(context["title_chain"]) > 0:
            ps0 = context.get("ps", [{}])[0]
            chain_paras = generate_chain_narrative(context["title_chain"], property_details=ps0, context=context)
            context["chain_paragraphs"] = chain_paras
            context["chain_text"] = "\n\n\t".join(chain_paras)
        elif context.get("chain_text"):
            context["chain_paragraphs"] = [p.strip() for p in context["chain_text"].split("\n\n") if p.strip()]
        else:
            context["chain_paragraphs"] = []
            context["chain_text"] = ""
```

- [ ] **Step 2: Verify generation logic**

Create a temporary script `scratch/test_generate.py` to verify splitting when manual mode is active:
```python
# scratch/test_generate.py
import sys
sys.path.append('.')

context = {
    "chain_is_manual": "true",
    "chain_text": "Para 1 text here.\n\nPara 2 text here.",
    "title_chain": [{"template_key": "SALE_DEED_PLOT"}]
}

# Emulate generate endpoint logic
if context.get("chain_is_manual") in ["true", True]:
    if context.get("chain_text"):
        context["chain_paragraphs"] = [p.strip() for p in context["chain_text"].split("\n\n") if p.strip()]
    else:
        context["chain_paragraphs"] = []

assert len(context["chain_paragraphs"]) == 2, f"Expected 2 paragraphs, got {len(context['chain_paragraphs'])}"
assert context["chain_paragraphs"][0] == "Para 1 text here."
assert context["chain_paragraphs"][1] == "Para 2 text here."
print("Generation check passed!")
```
Run: `python scratch/test_generate.py`
Expected: Print "Generation check passed!" without errors.

- [ ] **Step 3: Commit generate endpoint changes**

```bash
git add app.py
git commit -m "feat: bypass template compile in document generation when manual mode is active"
```

---

### Task 3: UI Integration and Reactive Boundary Sync

**Files:**
- Modify: `web_templates/case.html`

**Interfaces:**
- Consumes: DOM Events (`input`, `change`) on property fields
- Produces: Reactively updated timeline card previews and persistent state collection

- [ ] **Step 1: Update collectFieldData() in case.html to collect flag**

Modify the `"SD"` collection block in `collectFieldData()` to append `chain_is_manual`:
```javascript
            const data = {
                rd: document.getElementById('field_rd')?.value || '',
                sellers: [],
                buyers: [],
                ps: [],
                ws: [],
                chain: [],
                payments: [],
                chain_text: document.getElementById('field_chain_text')?.value || '',
                chain_is_manual: document.getElementById('field_chain_is_manual')?.checked ? 'true' : 'false'
            };
```

- [ ] **Step 2: Update initializeGlobalChainMode() to restore state on page load**

Modify `initializeGlobalChainMode()` in `case.html` (approx. line 2355) to restore the checkbox state from saved data:
```javascript
    function initializeGlobalChainMode() {
        const globalTextarea = document.getElementById('field_chain_text');
        const toggle = document.getElementById('field_chain_is_manual');
        if (!globalTextarea || !toggle) return;
        
        const isManualSaved = "{{ data.get('chain_is_manual', 'false') }}" === "true";
        toggle.checked = isManualSaved;
        
        if (isManualSaved) {
            globalTextarea.removeAttribute('readonly');
        } else {
            globalTextarea.setAttribute('readonly', 'true');
            
            // Standard fallback if narrative is empty but we have cards
            if (!globalTextarea.value.trim()) {
                const container = document.getElementById('chainCardsContainer');
                if (container) {
                    const textareas = container.querySelectorAll('textarea');
                    let paragraphs = [];
                    textareas.forEach(ta => {
                        if (ta.id !== 'field_chain_text' && ta.value && ta.value.trim()) {
                            paragraphs.push(ta.value.trim());
                        }
                    });
                    globalTextarea.value = paragraphs.join('\n\n');
                }
            }
        }
    }
```

- [ ] **Step 3: Add event listeners to property boundaries and fields**

Inside the `DOMContentLoaded` block in `case.html` (approx. line 1600), add the event listeners targeting property fields:
```javascript
        // Bind property fields for reactive chain sync
        const propertyFields = [
            'field_ps_0_adr', 'field_ps_0_area', 'field_ps_0_area_unit',
            'field_ps_0_e', 'field_ps_0_w', 'field_ps_0_n', 'field_ps_0_s'
        ];
        propertyFields.forEach(fieldId => {
            const el = document.getElementById(fieldId);
            if (el) {
                const triggerSync = () => {
                    const manualToggle = document.getElementById('field_chain_is_manual');
                    if (manualToggle && !manualToggle.checked) {
                        const container = document.getElementById('chainCardsContainer');
                        if (container) {
                            const cards = container.querySelectorAll('.chain-card');
                            cards.forEach((card, idx) => {
                                compileCardPreview(idx);
                            });
                        }
                    }
                };
                el.addEventListener('input', triggerSync);
                el.addEventListener('change', triggerSync);
            }
        });
```

- [ ] **Step 4: Commit case.html updates**

```bash
git add web_templates/case.html
git commit -m "feat: bind reactive property sync and collect chain_is_manual flag in UI"
```
