# RM Future Readiness Audit

## 1. RM Architecture Health

### RM Pipeline Mapping
*   **Extraction:** Handled in `modules/rm/extractor.py`. Utilizes Google Gemini via a monolithic, highly engineered prompt that attempts to extract all fields (borrowers, loans, properties, witnesses) in a single pass.
*   **Normalization:** Embedded directly within `extractor._normalize_response` and coupled with `utils/helpers.py`.
*   **Schema:** Implicit. Defined loosely by the structure expected in the prompt and enforced via the `prune_rm_data` function in `modules/rm/schema.py`. Heavy reliance on shorthand aliases (e.g., `bs`, `ls`, `ps`, `ws`).
*   **Context Generation:** Mixed into `app.py` under the `/case/<case_id>/generate` route. Business logic, fallback values, and padding are tightly coupled to the HTTP request cycle.
*   **Rendering:** Handled by `RMTemplateProcessor` in `modules/rm/processor.py` utilizing `docxtpl` for Jinja2 tag replacement inside `.docx` templates.
*   **Post-processing:** The processor dynamically converts Unicode Hindi strings into legacy DevLys 040 encodings prior to rendering, and includes logic for highlighting AI-generated/missing fields.

### Strengths
*   **Isolation:** The `modules/rm/` namespace correctly isolates RM-specific extraction and processing from Sale Deeds.
*   **Functional Viability:** The pipeline currently works for its specific, narrow use case (Registered Mortgages with 1-3 borrowers and 1-2 loans).
*   **Template Separation:** The presentation layer correctly lives in external `.docx` files.

### Weaknesses
*   **App.py Bloat:** Too much RM business logic (array padding, data massaging) happens inside the Flask route (`app.py`).
*   **Brittle Prompting:** Relying on a single massive prompt to perfectly map JSON objects makes the system vulnerable to hallucination and context-window degradation as document length increases.
*   **Alias Proliferation:** Extreme use of shorthand keys (`n`, `a`, `c`, `bs`, `ls`) reduces readability and increases cognitive load.

### Technical Debt
*   **Implicit Schemas:** The lack of strict Pydantic/dataclass models means data shapes are guaranteed only by scattered array padding logic.
*   **Fragmented Normalization:** Normalization logic spans the extractor, the processor, and generic helpers.
*   **Hardcoded Counts:** Array padding logic hardcodes limits (e.g., padding lists to exactly 10 to avoid Jinja errors).

---

## 2. RM vs SD Comparison

### Comparison Analysis
*   **Extractor Architecture:** Both are nearly identical in structure. SD is slightly more advanced, possessing a dedicated `extract_title_chain` method and specific property helper functions (`is_flat_property`).
*   **Schema Design:** Both suffer from the `bs`/`ss`/`ps` alias problem. SD has advanced to include a structured `title_chain` array, whereas RM relies on a simpler linear model.
*   **Processor Design:** `RMTemplateProcessor` and `SDTemplateProcessor` are functionally identical clones. Both perform DevLys conversion and highlighting.
*   **Template Design:** Both rely on `docxtpl` tags.

### Key Observations
*   **Where SD is cleaner:** Narrative generation. SD has extracted its title chain narrative logic into `modules/sd/narrative.py`.
*   **Where RM is cleaner:** Simplicity. RM does not have the complex and sometimes fragile chain-of-title event mapping that SD currently forces into a linear paradigm.
*   **Lessons from SD for RM:** RM needs to extract its narrative generation and context preparation out of `app.py` into dedicated modules (like SD's `narrative.py`).
*   **SD Mistakes Present in RM:** Rampant use of non-descriptive alias keys, monolithic extraction prompts, and context generation logic living inside the main Flask application file.

---

## 3. Future Document Types
*(Assuming: Lease Deed, Gift Deed, Will, Inheritance, Partition, Relinquishment, Settlement, Court Orders)*

### What Components are Generic?
*   AI Client instantiation and retry mechanisms (`genai` wrapper).
*   Document OCR / Image-to-Text extraction wrappers.
*   The Template Rendering Engine (`docxtpl` processing and highlighting).
*   The DevLys 040 Converter.

### What Components are RM-Specific?
*   Loan arrays (`ls`), Bank Signatory (`bsign`), specific Registered Mortgage extraction prompts.
*   The exact structure of the `session.json` specific to RM data.

### What Should Become Shared Infrastructure?
*   **Entity Extraction:** A generic `Person` extraction model (Name, Age, Relation, Address, ID) that isn't hardcoded as a "Borrower" or "Seller" in the prompt.
*   **Property Extraction:** A generic `Property` model that captures boundaries, addresses, and dimensions regardless of document type.
*   **Base Processor:** Unify `RMTemplateProcessor` and `SDTemplateProcessor` into a `LegalTemplateProcessor`.

### What Must Remain Document-Specific?
*   Legal phrasing generation (Narratives).
*   Business rules governing required parties (e.g., a Will requires a Testator, while a Partition requires multiple Co-owners).
*   Final mapping logic from generic entities to specific template tags.

---

## 4. Session Schema Readiness

### Review of `session.json`
*   **Support for Additional Types:** The current structure **cannot** cleanly support additional document types. The root keys are hardcoded to document-specific aliases (`bs` for buyers/borrowers, `ss` for sellers). A Will requires a "Testator" and "Beneficiary". Forcing them into `ss` and `bs` breaks semantic meaning.
*   **Schema Duplication:** `ss` (sellers), `bs` (buyers/borrowers), and `ws` (witnesses) duplicate the exact same `Person` schema structure (`n`, `a`, `c`, `relation_text`, `adr`, `id`, `pan`).
*   **Canonical Structures:** A canonical `Person` structure exists conceptually but is implemented ad-hoc in multiple places. The `Property` object (`ps`) is overly burdened with both flat and plot attributes simultaneously.
*   **Future Conflicts:** If a Settlement Deed requires 5 distinct party classes, the flat structure fails. The schema lacks an abstraction layer mapping generic parties to their document roles.

---

## 5. Shared Infrastructure Audit

### Review of Utils and Helpers
*   **Reusable Foundations:** `format_date_with_dots`, `amount_to_words`, `format_indian_currency`. The DevLys converter is robust and successfully isolated.
*   **Hidden Coupling:** `app.py` contains the `smart_merge` function, which contains hardcoded knowledge of specific list keys (`ls`, `ps`, `unassigned_aadhars`, `sellers`, `buyers`). This prevents generic list merging.
*   **RM/SD Leakage:** `normalize_relation_prefix` in `helpers.py` explicitly checks `if doc_type == "SD"`. This is a strict architectural violation where the shared utility layer has knowledge of downstream business implementations.

---

## 6. Top 20 Architectural Risks

1.  **Severity: High | Likelihood: High | Impact: High:** Monolithic `app.py` context generation. As new types are added, `app.py` will collapse under conditional `if doc_type == 'X'` statements.
2.  **Severity: High | Likelihood: High | Impact: High:** Schema Aliasing. Shorthand keys prevent code comprehension and cause data overwriting if keys collide across new document types.
3.  **Severity: High | Likelihood: High | Impact: High:** Leakage in `helpers.py`. Shared utilities knowing about `doc_type` prevents true modularity.
4.  **Severity: High | Likelihood: Medium | Impact: High:** Prompt Size Limits. Single-pass extraction prompts will fail on massive complex documents (e.g., multi-party Partition Deeds).
5.  **Severity: Medium | Likelihood: High | Impact: High:** Linear Title Chain limitations. Partition deeds and Wills create branching ownership graphs that the current `CHAIN_SCHEMA.md` array cannot support.
6.  **Severity: Medium | Likelihood: High | Impact: Medium:** Hardcoded Array Padding (e.g., padding to 10 to avoid Jinja errors) instead of robust template logic.
7.  **Severity: Medium | Likelihood: High | Impact: Medium:** `smart_merge` in `app.py` has hardcoded entity lists, breaking generic session management.
8.  **Severity: Medium | Likelihood: High | Impact: Medium:** `RMTemplateProcessor` and `SDTemplateProcessor` are duplicates. Maintaining DevLys logic in two places invites regression.
9.  **Severity: Medium | Likelihood: Medium | Impact: High:** AI hallucination of relation text mapping due to loose extraction rules.
10. **Severity: Medium | Likelihood: Medium | Impact: Medium:** Witness OCR Isolation logic is hardcoded and fragile, easily broken by minor name variations.
11. **Severity: Medium | Likelihood: Low | Impact: High:** No programmatic way to validate that a `.docx` template matches the data schema being passed to it.
12. **Severity: Low | Likelihood: High | Impact: Medium:** Relying on UI JSON payloads to strictly define session state without server-side Pydantic validation.
13. **Severity: Low | Likelihood: High | Impact: Medium:** Unassigned Aadhar logic is intertwined with business logic instead of being a discrete OCR step.
14. **Severity: Low | Likelihood: Medium | Impact: Medium:** Over-reliance on regex string replacement for normalization.
15. **Severity: Low | Likelihood: Medium | Impact: Low:** Inconsistent currency formatting edge cases in `helpers.py`.
16. **Severity: Low | Likelihood: Medium | Impact: Low:** File upload state management relies entirely on local filesystem folders without atomic locks.
17. **Severity: Low | Likelihood: Low | Impact: Medium:** Missing explicit API versioning for the Gemini clients.
18. **Severity: Low | Likelihood: Low | Impact: Low:** Synchronous API calls in Flask routes block the web thread.
19. **Severity: Low | Likelihood: Low | Impact: Low:** Fallback mechanism relies on hardcoded key rotation inside the extractor class.
20. **Severity: Low | Likelihood: Low | Impact: Low:** Lack of comprehensive automated unit test suite.

---

## 7. Top 20 Architectural Opportunities

1.  **Impact: High | Effort: Low | Risk: Low:** Move context generation logic out of `app.py` into `modules/rm/context_builder.py` and `modules/sd/context_builder.py`.
2.  **Impact: High | Effort: Medium | Risk: Low:** Unify `RMTemplateProcessor` and `SDTemplateProcessor` into a core `BaseTemplateProcessor`.
3.  **Impact: High | Effort: Medium | Risk: Medium:** Standardize a canonical `Person` schema and `Property` schema across all document types.
4.  **Impact: High | Effort: Medium | Risk: Medium:** Create an `Adapter` layer that translates canonical data into the legacy alias tags expected by `.docx` templates, preserving backward compatibility.
5.  **Impact: High | Effort: High | Risk: Medium:** Extract `smart_merge` from `app.py` and genericize it using explicit schema definitions.
6.  **Impact: Medium | Effort: Low | Risk: Low:** Remove `doc_type` switches from `utils/helpers.py` by making functions strictly pure.
7.  **Impact: Medium | Effort: Medium | Risk: Low:** Introduce Pydantic models for `session.json` to guarantee data integrity before rendering.
8.  **Impact: Medium | Effort: Medium | Risk: Low:** Break extraction prompts into multi-pass stages (e.g., Pass 1: Entities, Pass 2: Property, Pass 3: Rules) to improve accuracy.
9.  **Impact: Medium | Effort: High | Risk: Medium:** Develop a Graph-based representation of Title Chains to support future branching documents (Partition/Wills).
10. **Impact: Medium | Effort: Low | Risk: Low:** Abstract the Gemini API client into a core `LLMService` to remove redundancy across extractors.
11. **Impact: Medium | Effort: Low | Risk: Low:** Extract `unassigned_aadhars` logic into a generic Identity/KYC module.
12. **Impact: Low | Effort: Low | Risk: Low:** Standardize logging across modules instead of using print statements.
13. **Impact: Low | Effort: Low | Risk: Low:** Isolate the DevLys Converter completely and write a dedicated test suite for it to guarantee regression safety.
14. **Impact: Low | Effort: Medium | Risk: Low:** Create a template validation tool that parses a `.docx` and verifies that the `session.json` fulfills all required tags.
15. **Impact: Low | Effort: Medium | Risk: Low:** Move array padding (to 10) out of python code and into Jinja logic inside the master templates.
16. **Impact: Low | Effort: High | Risk: High:** Refactor Flask routes to use Blueprints for `sd/`, `rm/`, and `core/` to prevent monolithic scaling issues.
17. **Impact: Low | Effort: Medium | Risk: Low:** Implement async background jobs for AI extraction to prevent HTTP timeouts on large PDFs.
18. **Impact: Low | Effort: Low | Risk: Low:** Normalize Hindi string matching by creating a dedicated NLP utility class rather than inline Regex.
19. **Impact: Low | Effort: Medium | Risk: Low:** Standardize the concept of "Roles" so a `Person` can be dynamically mapped to `Seller`, `Buyer`, `Witness`, or `Testator` at runtime.
20. **Impact: Low | Effort: High | Risk: High:** Establish a formal data migration system for upgrading old `session.json` files when the schema evolves.

---

## 8. Recommended Roadmap

*(In accordance with AGENTS.md and MASTER_REMEDIATION_CONTEXT.md directives prioritizing safe debt reduction over immediate architectural rewrites)*

### Next Month: Decoupling the App Layer
*   **Goal:** Remove document-specific business logic from `app.py`.
*   **Action:** Create `context.py` inside `modules/rm/` and `modules/sd/`. Move array padding, variable aliasing, and data massaging into these files.
*   **Action:** Remove `doc_type` leakage from `utils/helpers.py`.
*   **Action:** Unify template processors if feasible without breaking RM/SD isolation constraints, or at minimum, synchronize them.

### Next Quarter: Canonicalization and Schema Abstraction
*   **Goal:** Protect the codebase from schema alias explosion while preserving the legacy Word templates.
*   **Action:** Define strict Pydantic/TypedDict schemas for canonical concepts (`Person`, `Property`, `Event`).
*   **Action:** Introduce an `Adapter` layer just before rendering. The core system speaks in canonical terms (`borrowers`, `name`, `address`), and the adapter translates it to legacy tags (`bs`, `n`, `adr`) solely for the `docxtpl` step.
*   **Action:** Break the monolithic extraction prompt into a two-pass system: KYC/Entity extraction first, Document Context extraction second.

### Before Introducing a Third Document Type (e.g., Lease Deed)
*   **Goal:** Ensure the framework handles generic routing and complex data shapes.
*   **Action:** Refactor `app.py` routing into generic endpoints that accept a `doc_type` and route to a registered pipeline class, completely removing `if doc_type == 'X'` from the HTTP layer.
*   **Action:** `session.json` must be restructured to support a generic `parties` array with assigned `roles` (e.g., `[{"role": "Lessor", "person": {...}}]`), supported by the aforementioned Adapter layer for legacy templates.
*   **Action:** Complete the Title Chain Graph investigation (On Hold in Master Context) to determine if linear arrays can support the new document type's historical requirements.