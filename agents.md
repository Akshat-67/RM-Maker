# Instructions for Future AI Agents (AGENTS.md)
 
> [!IMPORTANT]
> The guidelines below must be followed by all AI coding assistants or agents working on this codebase. This is a production legal document automation system. **Understand before editing. Avoid blind rewrites.**

## 1. Project Purpose & Architecture
RM-Maker is a production legal document automation system designed to extract entity data from KYC files, manage template schedules, and compile Registered Mortgage (RM) and Sale Deed (SD) documents.

The core pipeline follows this sequence:
```
Upload → Extraction → Schema Validation → Processing → Template Context Generation → docxtpl Rendering
```

*   **Fact Extraction**: AI models extract structured factual data only.
*   **Deed Generation**: Templates (`.docx`) own the legal wording; code only passes variable contexts.
*   **Hindi Font Paradigm**: 
    - Unicode internally.
    - Legacy DevLys conversion only at docx rendering boundary.
    - Do not force legacy fonts globally.

---

## 2. Code Protection and Core Constraints

### High Impact Files (Extra Care Required)
High impact files require extra care:
*   [modules/rm/](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/modules/rm/) (all scripts under RM module)
*   [modules/sd/](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/modules/sd/) (all scripts under SD module)
*   [utils/helpers.py](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/utils/helpers.py)
*   [app.py](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/app.py) (specifically session routes)
*   [web_templates/case.html](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/web_templates/case.html)

Before modifying:
*   inspect dependencies
*   preserve schema compatibility
*   understand historical reasons

### Registered Mortgage (RM) Stability
*   **Stability**: The RM pipeline is highly stable and production-hardened.
*   **Compatibility**: Preserve backward compatibility. Avoid making changes to RM schema, processors, or extractors unless explicitly requested.

### Sale Deed (SD) Canonical Shorthands
Preserve the shorthand list names for SD cases in session databases:
*   `ss` = sellers
*   `bs` = buyers
*   `ws` = witnesses
*   `ps` = property

### Universal Digit conversion
*   Devanagari numerals (`०-९`) must always be converted to standard English digits (`0-9`) globally (applied at session loading, session saving, and AI extraction).

### Typographic UI Rules
*   The web interface must display Hindi in clean Unicode Devanagari fonts (e.g. `Segoe UI` or `Mangal`). Legacy non-Unicode fonts (e.g. `DevLys 010`, `Kruti Dev`) must **never** be used for browser styling/textareas.

### Real-Time Transliteration
*   Do not modify the automatic English-to-Hindi transliteration flow on Enter/Tab/blur fields calling `/transliterate` or the local `Sanscript` fallback.

---

## 3. Editing and Refactoring Rules
*   **Historical Code Preservation**: Historical code may look unusual because it fixes real legal workflow edge cases. Do not simplify without understanding why it exists.
*   **Serena Integration**: Use Serena symbol search or get file/symbol overviews before executing edits.
*   **Check Callers**: Inspect caller references before changing function signatures. Explain design impacts.
*   **Smallest Safe Changes**: Prefer incremental modifications and write surgical replacement blocks rather than full-file rewrites.
*   **Session Integrity**: Never silently drop data fields. Saved field structures are contracts; schema changes must include backward-compatible migrations.
*   **Templates as Contracts**: Pre-defined placeholders inside `.docx` master files are API contracts. Never remove context keys without verifying all templates and files first.

---

## 4. Graphify Usage
Graphify is available as a generated repository analysis, not as an MCP.

Before major changes inspect `graphify-out`.

Use Graphify data for:
*   dependency analysis
*   identifying high impact files
*   finding connected modules
*   understanding architecture clusters
*   refactor planning

Required before:
*   moving functions/classes
*   changing schemas
*   changing processors
*   modifying `app.py`
*   modifying shared utilities

Workflow:
1.  Use Serena MCP for live code symbols.
2.  Use `graphify-out` for dependency impact.
3.  Make changes only after understanding both.

Do not assume Graphify is automatically available. Read the generated files.

---

## 5. Permanent Engineering Policy & Definition of Done

This section outlines the strict requirements for regression testing, documentation updates, and the Definition of Done (DoD) for all tasks.

### Regression Test Policy

Automated tests are first-class project assets.

Whenever production code changes:
- determine whether existing pytest tests still cover the modified behavior
- determine whether existing Playwright tests still cover the modified behavior
- update affected tests when intended behavior changes
- add regression tests for:
    - new features
    - bug fixes
    - new services
    - new routes
    - schema changes
    - document generation changes

Never leave production changes without corresponding test updates.

Every production bug fix must include a regression test reproducing the original issue.

A task is not complete until relevant tests pass.

### Documentation Policy

Whenever architecture changes:
- update AGENTS.md if workflow rules changed
- update agent_knowledge if architecture changed
- update architecture documentation if needed
- recommend regenerating Graphify whenever dependency relationships change significantly

### Definition of Done

A task is complete only when:

✓ implementation complete

✓ architecture preserved

✓ RM compatibility verified

✓ SD compatibility verified

✓ relevant pytest tests pass

✓ relevant Playwright tests pass

✓ regression tests updated

✓ documentation updated if architecture changed

✓ Serena memories updated if long-term project knowledge changed

✓ Graphify regenerated when dependency relationships materially change

### Future Development Engineering Workflow

For any future task, the development lifecycle must follow this sequence:

```
    Request
       ↓
Serena memories (review existing rules & contexts)
       ↓
Graphify architecture review (for non-trivial changes, inspect graphify-out)
       ↓
Architecture analysis
       ↓
Implementation
       ↓
Pytest (verify Python logic and backend pipelines)
       ↓
Playwright (verify frontend and portal autofill behaviors)
       ↓
Documentation update (sync AGENTS.md / agent_knowledge if architecture changed)
       ↓
Serena memory update (store long-term rules/decisions)
       ↓
Graphify regeneration (when architecture changes, run `graphify update .`)
       ↓
 Task complete
```

