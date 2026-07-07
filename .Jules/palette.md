## 2026-06-18 - Missing ARIA Labels on Icon-only Buttons
**Learning:** Found that multiple icon-only buttons (`✨`, `🔄`, `✖`) within the `web_templates/case.html` template lacked `aria-label` or `title` attributes, making them inaccessible to screen readers.
**Action:** Next time inspecting web templates, proactively check for standalone emojis or icons used as buttons without accompanying accessible text, and add `aria-label` and `title` to them.
## 2024-07-28 - Adding labels and ARIA to interactive elements
**Learning:** In Jinja templates where custom CSS elements like hamburger menus or close buttons are built without semantic HTML tags, applying `aria-label` and correct `for` bindings for input groups is critical for screen reader accessibility, as the visual structure alone does not convey interactivity to assistive tech.
**Action:** Always add `aria-label` to custom icon buttons and explicitly bind labels to inputs using the `for` attribute in newly created components to maintain accessibility without requiring layout shifts.
