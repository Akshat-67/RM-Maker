# Verification Progress & Compile Safety Gates

Verification Progress tracking provides real-time completeness visibility and gates document compile generation to avoid legal errors.

## Overall Progress Bar
- Rendered inline within the unified compact control bar of `components/review.html`.
- Displays dynamic progress text: `Verified: X / Y fields (P%)`.
- Re-calculates on verification state changes (`onchange` on `.verify-check` elements).

## Section Tab Completion Badges
- Completion indicators are displayed on each Verification sub-tab:
  - Parties: `badge-parties`
  - Witnesses: `badge-witnesses`
  - Property: `badge-property`
  - Loans: `badge-loans`
  - Schedules: `badge-schedules`
- Displays `X/Y` (incomplete) or `✓ X/Y` (complete) and switches CSS styling `.tab-badge-complete` (green) / `.tab-badge-incomplete` (gray) dynamically.

## Compile Safety Gate & Ready Indicator
- Disables the "Verified: Generate Final Document" compiling buttons (`generateRM()` or `generateSD()`) if critical fields are unchecked.
- Tooltips display list of missing critical fields.
- Mode-aware critical path mapping:
  - **RM**: Borrower names/Aadhars, Signer names, and Property Address.
  - **SD**: Seller names, Buyer names, Property Address, and Consideration Amount.
- Changes button to active green (`btn-success`) with a success message once cleared.
