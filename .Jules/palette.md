## 2026-06-18 - Missing ARIA Labels on Icon-only Buttons
**Learning:** Found that multiple icon-only buttons (`✨`, `🔄`, `✖`) within the `web_templates/case.html` template lacked `aria-label` or `title` attributes, making them inaccessible to screen readers.
**Action:** Next time inspecting web templates, proactively check for standalone emojis or icons used as buttons without accompanying accessible text, and add `aria-label` and `title` to them.
## 2026-07-24 - Dynamic button loading states
**Learning:** When injecting Bootstrap loading spinners into buttons during async operations, it is crucial to save and restore `innerHTML` rather than `textContent`.
**Action:** Always capture the original `innerHTML` of a button before replacing its contents with a spinner, and restore using `innerHTML` to preserve existing icons and HTML formatting.
