## Phase 1 Refactor Progress

### Completed
- services/session_manager.py created with:
  - CASES_DIR constant
  - title_case_address()
  - normalize_amount_in_words()
  - list_cases()
  - sync_template_keys_to_property_type()
  - load_case_session()
  - prune_case_data()
  - save_case_session()
  - All imports: os, json, time, re, convert_hindi_digits_to_english
  - Lazy imports: modules.rm.processor, modules.sd.schema, modules.rm.schema

- services/file_service.py created with:
  - TEMPLATES_DIR constant
  - discover_templates()
  - smart_merge()
  - delete_case_directory()
  - resolve_case_file_path()
  - save_uploaded_file_to_bucket()
  - remove_file_from_disk()

### Architecture Rules Enforced
- No Flask objects in services (request, jsonify, decorators)
- Routes handle HTTP, services handle logic
- RM/SD domain modules untouched
- Function signatures preserved identically
- app.py imports from services

### Changed Imports in app.py
- from services.session_manager import (...)
- from services.file_service import (...)
- Local definitions removed, replaced by imports