## 2026-06-18 - Missing ARIA Labels on Icon-only Buttons
**Learning:** Found that multiple icon-only buttons (`✨`, `🔄`, `✖`) within the `web_templates/case.html` template lacked `aria-label` or `title` attributes, making them inaccessible to screen readers.
**Action:** Next time inspecting web templates, proactively check for standalone emojis or icons used as buttons without accompanying accessible text, and add `aria-label` and `title` to them.
## 2026-06-30 - Tooltips for btn-close Elements
**Learning:** Found that `.btn-close` components across `web_templates/case.html`, `web_templates/template_builder.html`, and `web_templates/devlys_to_unicode.html` used `aria-label` but lacked `title` tooltips for sighted users. In `template_builder.html`, the modal close button was completely missing the `aria-label`.
**Action:** When adding `.btn-close` elements (or updating legacy templates), always ensure both `aria-label` and `title` are explicitly set (e.g., `aria-label="Close" title="Close"`) to support both screen readers and hover states.
