# Agent Knowledge: Decisions

This memory summarizes core design choices and engineering guidelines documented in [decisions.md](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/agent_knowledge/decisions.md).

## Core Decisions
1.  **AI Extracts, Templates Draft**: AI engines extract facts into structured JSON. Templates (`.docx`) own all legal text, structures, and formatting.
2.  **Unicode-Internal, Legacy-External**: 
    - Unicode internally.
    - Legacy DevLys conversion only at docx rendering boundary.
    - Do not force legacy fonts globally.
    - Rationale: Legacy encodings break browser rendering, input fields, spelling checks, and HTML layouts. Restricting legacy fonts to docx compiler files ensures web verification views stay clean, responsive, and readable.
3.  **RM/SD Pipeline Separation**: Maintain strict separation between `modules/rm/` and `modules/sd/` to preserve stable RM code when editing SD code.
4.  **Schemas as API Contracts**: Existing JSON keys must never be dropped or silently deleted. Backward compatibility and migrations must be maintained.
5.  **UI Verification Prior to Automation**: Browser autofill automation depends on manual validation of AI data in the verification dashboard.
6.  **Real Legal Workflow Preservation**: Historical code may look unusual because it fixes real legal workflow edge cases. Do not simplify or refactor it away without fully understanding why it exists.
