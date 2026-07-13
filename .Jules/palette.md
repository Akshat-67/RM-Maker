## 2026-06-18 - Missing ARIA Labels on Icon-only Buttons
**Learning:** Found that multiple icon-only buttons (`✨`, `🔄`, `✖`) within the `web_templates/case.html` template lacked `aria-label` or `title` attributes, making them inaccessible to screen readers.
**Action:** Next time inspecting web templates, proactively check for standalone emojis or icons used as buttons without accompanying accessible text, and add `aria-label` and `title` to them.

## 2026-07-13 - Add ARIA Labels to Mobile Menu Buttons
**Learning:** The hamburger menu button (`☰`) present across multiple templates (`case.html`, `dashboard.html`, `devlys_to_unicode.html`, and `template_builder.html`) lacked `aria-label` and `title` attributes. Without an accessible name, screen readers announce this simply as "button".
**Action:** Always verify that all icon-only interactive elements (like custom hamburger menus) have explicit `aria-label` and `title` attributes.
