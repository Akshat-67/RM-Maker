# Instructions for Coding Agents (AGENTS.md)

This document is the primary entry point and navigation hub for AI coding assistants working on the RM-Maker repository. 

> [!IMPORTANT]
> RM-Maker is a production legal document automation system. Understand the architecture, design patterns, and constraints before editing. Avoid blind rewrites.

---

## 1. Repository Philosophy
When modifying this codebase, follow these core principles:
- **Long-lived Production App**: RM-Maker is a stable, production-hardened system. Prioritize backward compatibility and stability.
- **Extend, Don't Rewrite**: Extend existing systems and architectures rather than rewriting modules from scratch.
- **Incremental & Surgical Changes**: Write clean, surgical replacement blocks. Prefer minimal, focused changes over full-file rewrites.
- **Maintainability Over Cleverness**: Code must be clear and readable. Avoid unnecessary complexity or introducing unrequested frameworks.
- **Data Integrity**: Runtime data structures (such as session schemas) are contracts. Never silently drop or modify data fields.

---

## 2. Permanent Engineering Constraints

- **Unicode-First Processing**: All internal data processing, storage, and UI states use Unicode Devanagari. Legacy font encoding is applied *only* at the document rendering boundary.
- **Standardized Digits**: Devanagari numerals (`०-९`) must be converted to standard English digits (`0-9`) globally (during extraction, load, and save).
- **Hindi Segment Parsing**: Salutations and relative prefixes must be normalized and split cleanly in session schemas.
- **UI Typography**: Web interfaces must display Hindi in Unicode fonts (e.g. Segoe UI, Mangal). Legacy fonts (e.g. DevLys, Kruti Dev) are never used for browser layout or styling.

---

## 3. Documentation Map (Where to Read)
Depending on your task, you MUST read the corresponding design document before modifying code:

| If your task involves... | Read this document... |
| :--- | :--- |
| Core architecture, files, or high-level pipeline flow | [docs/ARCHITECTURE.md](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/docs/ARCHITECTURE.md) |
| Modifying Registered Mortgage (RM) templates, logic, or processor | [docs/RM_PIPELINE.md](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/docs/RM_PIPELINE.md) |
| Modifying Sale Deed (SD) templates, schemas, timeline, or narrative engine | [docs/SD_PIPELINE.md](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/docs/SD_PIPELINE.md) |
| Customizing the e-Panjiyan Chrome extension or autofill selectors | [docs/CHROME_EXTENSION.md](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/docs/CHROME_EXTENSION.md) |
| Tweaking AI fact extraction, pre-filtering pages, or auto-cropping | [docs/EXTRACTION.md](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/docs/EXTRACTION.md) |
| Running backend/E2E test suites or updating tests | [docs/TESTING.md](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/docs/TESTING.md) |

---

## 4. Development Workflow
For any task, follow this sequential workflow:

```
Read AGENTS.md (Root navigation hub)
       ↓
Read relevant documentation under /docs
       ↓
Inspect affected files and their dependencies
       ↓
Implement changes (surgical & modular)
       ↓
Run relevant Pytest / Playwright tests
       ↓
Update documentation if architecture changed
       ↓
Update Serena memories if long-term architecture changed
```

---

## 5. Definition of Done (DoD)
A task is complete only when:
- [ ] Implementation is complete and code matches the requested specifications.
- [ ] Existing application behavior is preserved and stable.
- [ ] Relevant unit and integration tests pass successfully.
- [ ] Regression tests are added for any new features or bug fixes.
- [ ] Documentation is updated if architectural elements or rules changed.
- [ ] Serena memories are updated if long-term architectural knowledge changed.
