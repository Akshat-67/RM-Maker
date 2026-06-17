# Productivity Improvement Report

## 1. Executive Summary
The LegalDoc Automator Pro is functionally complete, but currently optimized for *single* case processing. For an office worker processing 50 documents a day, the cumulative time lost to "navigation navigation" (returning to dashboard) and "scrolling fatigue" (finding the generate button) is approximately **60-90 minutes per day**.

---

## 2. Productivity Recommendations

### ⚡ Quick Wins (< 1 hour)
#### 1. Auto-Focus Search on Dashboard
- **Current:** Page loads -> user moves mouse -> clicks search bar -> types.
- **Improved:** Page loads -> input focused.
- **Time Saved:** 2-3 seconds per case lookup.
- **Impact:** Medium.

#### 2. Visual "Unsaved Changes" Indicator
- **Current:** User edits a field and isn't sure if it's saved. Redundant "Save Workspace" clicks.
- **Improved:** Add a standard `(*)` to the page title or change Save button color when inputs differ from session state.
- **Time Saved:** Reduces redundant clicks and "save-anxiety".
- **Impact:** High.

---

### 🚀 High Impact (< 1 day)
#### 1. Next / Previous Case Navigation (Sequential)
- **Current:** Open Case 1 -> [Verify] -> Back to Dashboard -> Find Case 2 -> Open Case 2.
- **Improved:** `[← Prev Case]` `[Next Case →]` buttons in the header.
- **Keyboard Shortcut:** `Alt + Left` / `Alt + Right`.
- **Time Saved:** 10-15 seconds per case transition. (50 cases = 10+ minutes saved daily).
- **Impact:** CRITICAL for batch processing.

#### 2. Dashboard Status Badges
- **Current:** Cases are just IDs and names. User must "hunt" for cases that need verification.
- **Improved:** Badges for `Needs AI`, `AI Extracted`, `Verified`, `Missing Template`.
- **Time Saved:** 5 minutes per batch by allowing work prioritization.
- **Impact:** High.

#### 3. Sticky Generation Header
- **Current:** Generate button is at the extreme bottom. SD cases with 5+ sellers require 3 full mouse wheel scrolls to find it.
- **Improved:** Keep "Save", "Generate", and "Case Status" in a sticky top bar within the Workspace.
- **Time Saved:** 5 seconds of scrolling per document.
- **Impact:** High.

---

### 🛠 Major Improvements (< 1 week)
#### 1. Template Builder: Click-to-Assign
- **Current:** Copy document text -> Scroll to Manual Add -> Select Tag -> Click Add.
- **Improved:** Clicking a tag in the Catalog automatically pre-selects it and focuses the "Manual Key" input.
- **Time Saved:** 5 seconds per mapping.
- **Impact:** High for template maintainers.

#### 2. Bulk Action Dashboard
- **Current:** Delete case, Generate doc, etc. is 1-by-1.
- **Improved:** Checkboxes on dashboard for bulk Delete or bulk Generate (if already verified).
- **Time Saved:** 10 minutes per batch.
- **Impact:** Medium.

---

## 3. Power-User Workflow: "The 3-Minute Deed"
With these improvements, a power user workflow becomes:
1. `Dashboard` -> Search focuses -> Open Case 1.
2. `Verify All` -> `Ctrl + S` -> `Ctrl + Enter` (Generate).
3. `Alt + Right` -> Instant transition to Case 2.
4. **Total Mouse Travel:** Nearly Zero.
5. **Total Page Loads:** 1 (instead of 2 per case).

**Total Daily Savings:** ~45-60 minutes per employee.
