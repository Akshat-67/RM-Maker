# Bulk Verification & Undo Support

To streamline verification for dense cases, the workspace implements two levels of bulk verification with full undo support.

## Verify Section
- A "Verify Section" action button replaces the generic "Verify All" button in the compact control bar.
- Triggers `verifySection()` which selects all `.verify-check` elements within the active `.tab-pane` and checks them.
- Can be activated via keyboard shortcut **Alt+A**.

## Verify Category
- High-level categories (represented by `.card` components e.g. Borrower cards, Witness cards, Loan cards, Property cards) are dynamically decorated with a `✓ Verify Category` badge on page load via `addVerifyCategoryButtons()`.
- Triggers `verifyCategory()` which selects all `.verify-check` elements strictly inside that card element and checks them.

## Undo Support
- Running a bulk operation (Section or Category) stores the pre-action states of all affected checkboxes in a global variable `lastBulkActionState`.
- Renders an informative notification banner (`#bulkUndoBanner`) with the counts of fields bulk verified and an active "Undo" button.
- Re-checking or pressing **Ctrl+Z** calls `undoLastBulkAction()` which restores the checkboxes to their exact prior states and updates verification metrics in real-time.
