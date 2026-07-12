# Keyboard-First Workflow Shortcuts

To maximize clerk throughput and minimize repetitive mouse actions, the verification workspace implements keyboard-first triggers.

## Global Hotkey Mappings
- **Alt+N**: Focuses the next unverified input field (`input[id^="field_"]` or `textarea[id^="field_"]`) in the active tab section. Wraps around automatically and triggers page-snapping preview of the newly focused field.
- **Alt+V**: Toggles the verification state (checked/unchecked) of the currently focused input. Dispatches a `'change'` event to trigger instant progress recalculations and compile safety check evaluations.
- **Ctrl+S**: Programmatically triggers the global `saveCase()` function to save verification progress.
- **Ctrl+Enter**: Compiles the final document if the compile safety gate is open (by clicking the active `generateRM()` or `generateSD()` button).

## Input Navigation Ergonomics
- Verification checkboxes (`.verify-check`) have `tabIndex = -1` dynamically applied during initialization. This allows clerks to press `Tab` to navigate strictly between text fields, bypassing checkboxes.
