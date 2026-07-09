# Architectural Decisions Log (decisions.md)

This log documents core architectural decisions, design choices, and engineering guidelines governing LegalDoc Automator.

---

## 1. Fact Extraction vs. Template Drafting
*   **Decision**: AI models must extract raw facts and structured parameters only. Word templates (`.docx`) own all legal language, headers, structures, and static text.
*   **Rationale**: Placing legal wording inside the code makes it brittle and hard for legal teams to update. Keeping it in template documents allows business owners to modify terms directly inside Microsoft Word without altering python code.
*   **Exception**: Title chain narratives (since they compile historical details from many events) are dynamically built in Hindi, but they rely on templates defined in code rather than ad-hoc generation.

---

## 2. Unicode-Internal, Legacy-External Font Paradigm
*   **Decision**: 
    - Unicode internally.
    - Legacy DevLys conversion only at docx rendering boundary.
    - Do not force legacy fonts globally.
*   **Rationale**: Legacy encodings break browser rendering, input fields, spelling checks, and HTML layouts. Restricting legacy fonts to docx compiler files ensures web verification views stay clean, responsive, and readable.

---

## 3. Registered Mortgage (RM) and Sale Deed (SD) Isolation
*   **Decision**: RM and SD pipelines must remain isolated in separate files and directory paths (`modules/rm/` vs. `modules/sd/`).
*   **Rationale**: While they share utility functions, they represent different transaction structures, have distinct schemas, and serve independent templates. Separating them prevents regressions in the stable RM system when modifying the developing SD system.

---

## 4. Schemas are API Contracts
*   **Decision**: The session case schemas are treated as API contracts. Existing saved fields must never be deleted, modified, or silently dropped.
*   **Rationale**: Modifying schemas without providing migration paths breaks compatibility with existing session files, corrupts loading in the UI, and results in application crashes.
*   **Constraint**: Shorthand collections in SD (`ss`, `bs`, `ws`, `ps`) must be preserved.

---

## 5. UI-Driven Validation Prior to Automation
*   **Decision**: The browser automation tools rely on manual verification first. Case data is extracted and reviewed on the verification UI before the browser extensions auto-populate forms on e-Panjiyan.
*   **Rationale**: Unverified AI extraction results could lead to legal errors if submitted directly to state portals. A human-in-the-loop stage provides essential checks before final submission.

---

## 6. Real Legal Workflow Preservation
*   **Decision**: Historical code may look unusual because it fixes real legal workflow edge cases. Do not simplify or refactor it away without fully understanding why it exists.
*   **Rationale**: Legal documents and government forms have rigid and sometimes counter-intuitive validation requirements. Code that looks redundant or sub-optimal is often a highly targeted patch that solves a specific platform or registry edge case.
