## 2026-06-18 - Missing ARIA Labels on Icon-only Buttons
**Learning:** Found that multiple icon-only buttons (`✨`, `🔄`, `✖`) within the `web_templates/case.html` template lacked `aria-label` or `title` attributes, making them inaccessible to screen readers.
**Action:** Next time inspecting web templates, proactively check for standalone emojis or icons used as buttons without accompanying accessible text, and add `aria-label` and `title` to them.

## 2026-06-24 - Missing Loading States on Async UI Actions
**Learning:** Document generation actions (`generateRM()`) didn't disable the trigger button or show loading state, risking duplicate submissions and feeling unresponsive.
**Action:** When adding new template buttons that trigger asynchronous endpoints (like `fetch`), always add a Bootstrap loading spinner and disable the button to provide clear visual feedback and prevent double-clicks.
