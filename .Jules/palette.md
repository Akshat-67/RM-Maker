## 2026-06-18 - Missing ARIA Labels on Icon-only Buttons
**Learning:** Found that multiple icon-only buttons (`✨`, `🔄`, `✖`) within the `web_templates/case.html` template lacked `aria-label` or `title` attributes, making them inaccessible to screen readers.
**Action:** Next time inspecting web templates, proactively check for standalone emojis or icons used as buttons without accompanying accessible text, and add `aria-label` and `title` to them.

## 2026-07-14 - Missing ARIA Labels on Mobile Menu Triggers and Modals
**Learning:** Found that custom layout elements like the `.mobile-menu-trigger` hamburger icon and `.btn-close` modal close buttons lacked semantic `aria-label`s, making critical navigation paths completely inaccessible to screen readers.
**Action:** Always add descriptive `aria-label` attributes to custom interactive UI elements that use symbols/icons (e.g. `☰`, `×`) instead of text content, particularly for navigation and modal controls.
