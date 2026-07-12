# Agent Knowledge: Fragile Systems

This memory lists sensitive parts of the repository detailed in [fragile_systems.md](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/agent_knowledge/fragile_systems.md).

## Critical Risk Zones
- **Document run splitting**: Regular expression filters in python-docx formatting split runs based on font types. Editing this logic can corrupt document styles or cause replacement bugs.
- **e-Panjiyan DOM selectors & AJAX timings**: Selectors in extension scripts (`content.js`) are vulnerable to changes on `epanjiyan.nic.in`. AJAX requests require wait timeouts.
- **`case.html` UI scripts**: High-volume jQuery/JavaScript handles unassigned Aadhaar dragging, witness arrays, and role mapping. Small edits can cause serialization mismatch errors.
- **Session saving (`app.py`)**: Parallel save queries to the JSON sessions can lead to data loss. Keep database rows synchronized with file case IDs.
- **AI extraction prompts**: Subtle prompt shifts in extractor modules can break the schema shape of returned JSON keys.
- **RM unassigned_aadhars & Relation Behavior**:
  - Aadhaar scans are funneled exclusively into `unassigned_aadhars` list on the backend and verified via the `case.html` client interface.
  - The relation parameters `r` (relation type, e.g. `S/o`, `W/o`) and `rn` (relative name) must remain fully populated on `unassigned_aadhars`, borrowers (`bs`), and witnesses (`ws`), and preserved in `prune_rm_data` to ensure template compatibility.
  - Changing how these fields are handled in the UI or schema pruning will break the drag-and-drop assignment or the custom Jinja `basename` filter in `case.html` templates.
