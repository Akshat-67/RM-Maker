## 2026-06-18 - Missing ARIA Labels on Icon-only Buttons
**Learning:** Found that multiple icon-only buttons (`✨`, `🔄`, `✖`) within the `web_templates/case.html` template lacked `aria-label` or `title` attributes, making them inaccessible to screen readers.
**Action:** Next time inspecting web templates, proactively check for standalone emojis or icons used as buttons without accompanying accessible text, and add `aria-label` and `title` to them.

## 2026-06-27 - Added Missing Loading States
**Learning:** Encountered buttons for critical, asynchronous actions ("Apply Assignments" and "Generate Document") lacking disabled and loading states, resulting in potential for confusing multiple-submissions.
**Action:** When inspecting async functions triggered via UI interactions, ensure appropriate `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>` states and `disabled=true` toggles are applied to the triggering buttons.