---
milestone: Web UI Migration, Case Management & Aadhaar Automation
version: 5.0.0
updated: 2026-05-30T13:24:00Z
---

# Roadmap

> **Current Phase:** 1 - Stability & Harmonization of Web Architecture
> **Status:** executing

## Must-Haves (from SPEC)

- [ ] Flask Web Server serving Case Dashboard and Dual-Panel Workspace
- [ ] Session persistence, save, and load for cases in `cases/<case_id>/session.json`
- [ ] Multimodal AI extraction with Aadhaar extraction rules and unassigned Aadhaar queue
- [ ] Interactive Aadhaar Role Assignment table in case UI
- [ ] In-memory Word post-render highlighter preserving header/footer styling

---

## Phases

### Phase 1: Stability & Harmonization of Web Architecture
**Status:** 🔄 In Progress
**Objective:** Stabilize the Flask architecture, eliminate Tkinter leftovers, integrate the dual-panel Flask workspace, and harmonize CSS/JS with dynamic AI model loading.
**Requirements:** SPEC goals 1 & 2

**Plans:**
- [x] Plan 1.1: Web Interface Foundations & Case Sessions
- [ ] Plan 1.2: Stabilize Web UI Logic & Refinement

---

### Phase 2: Aadhaar Guided OCR & Smart Role Mapper
**Status:** ⬜ Not Started
**Objective:** Fully integrate the dynamic Aadhaar role mapper UI and verify parentage/salutations formatting.
**Depends on:** Phase 1

**Plans:**
- [ ] Plan 2.1: Aadhaar OCR Logic Integration
- [ ] Plan 2.2: Interactive Role Mapping Table and Auto-Verification

---

### Phase 3: Robust Calculations & Smart Merging
**Status:** ⬜ Not Started
**Objective:** Implement incremental extraction and smart-merging utilities to protect user verification edits.
**Depends on:** Phase 2

**Plans:**
- [ ] Plan 3.1: Non-Destructive Smart Merge logic
- [ ] Plan 3.2: Verification and Highlights Engine

---

## Progress Summary

| Phase | Status | Plans | Complete |
|-------|--------|-------|----------|
| 1 | 🔄 | 0/2 | — |
| 2 | ⬜ | 0/2 | — |
| 3 | ⬜ | 0/2 | — |

---

## Timeline

| Phase | Started | Completed | Duration |
|-------|---------|-----------|----------|
| 1 | 2026-05-30 | — | — |
| 2 | — | — | — |
| 3 | — | — | — |
