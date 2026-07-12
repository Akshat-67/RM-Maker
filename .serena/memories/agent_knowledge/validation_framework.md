# Validation Framework Implementation

The validation framework acts as a scalable domain-based checker for identifying contradictions, format errors, and duplicate entries in case data.

## Phase 1: Core Framework Structure (`services/validation/`)
- `base.py`: Defines abstract class `BaseValidator` with `.supports(doc_type)` and `.validate(case_data)`.
- `models.py`: Defines data-transfer objects `FixAction`, `Discrepancy`, and `ValidationResult`.
- `registry.py`: Implements a runtime `ValidatorRegistry` with a central global registry instance.
- `engine.py`: Defines `ValidationEngine` that runs active supporting validators, catches crashes safely, and returns the aggregated result.

## Phase 2: Domain Validator (`identity_validator.py`)
- First registered validator in the pipeline.
- Implements:
  - **Aadhaar format**: Checks if raw digits of `id` have length 12.
  - **Aadhaar checksum**: Implements the **Verhoeff algorithm** using Multiplication (D) and Permutation (P) tables to validate check digits.
  - **PAN format**: Validates alphanumeric string syntax against standard Indian PAN regex.
  - **Duplicate Aadhaar**: Flags if identical Aadhaar strings are found on multiple parties in the case.
  - **Duplicate PAN**: Flags if identical PAN strings are found on multiple parties.

## Phase 3: Route Integration (`routes/cases.py`)
- Exposes route `GET /api/case/<case_id>/validation` which triggers validation on the saved session state and returns a `ValidationResult` JSON dictionary.

## Phase 4: Frontend Case Health Badge
- Embedded `#caseHealthBadge` next to overall progress bar.
- On save or verification change, calls `fetchAndUpdateCaseHealth()` which fetches validation data:
  - **🟢 Ready** (bg-success) if `is_valid` is true.
  - **⚠️ Issues Found** (bg-warning) if validation errors are detected.
