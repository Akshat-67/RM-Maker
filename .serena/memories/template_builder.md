# Template Builder System Memory

The Template Builder is a desktop utility used to map raw `.docx` legal document templates into standardized Jinja-syntax files.

## Key Files
- Tkinter App: [template_builder.py](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/template_tools/template_builder.py) (The GUI application).
- Core Engine: [builder_core.py](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/template_tools/builder_core.py) (Document manipulation functions, cell and paragraph traversal, text replacement).
- Master Mapping: [MASTER_FIELD_MAPS.json](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/template_tools/MASTER_FIELD_MAPS.json) (Standard fields catalog).
- Tags Reference: [TAGS_REFERENCE.md](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/template_tools/TAGS_REFERENCE.md).

## Operational Workflow
1. **Load Template**: User opens a standard Word document (`.docx`).
2. **Field Cataloging**: The builder displays all standard legal tags defined in `builder_core.py` (for both RM and SD modes).
3. **Replacement & Tagging**:
   - Searches for target texts inside paragraphs and table cells.
   - Replaces literal placeholders (e.g. "Borrower Name") with Jinja expressions (e.g. `{{bs[0].n}}`).
   - Merges contiguous runs with identical formatting to prevent split-tags inside XML files (handled via `DocManipulator`).
4. **Export Master Template**: Saves the compiled `.docx` to the appropriate bank/scheme subfolder inside `templates/`.
