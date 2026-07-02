# Enterprise SaaS Redesign Plan

## 1. The Prime Directive
The current frontend is a functional prototype. Your mission is to perform a **complete visual redesign from first principles**. Do not simply polish or refactor the existing CSS. You must dismantle the current layouts and rebuild them to match the aesthetic caliber of products like **Linear, Vercel, Raycast, Stripe, and Apple**.

### Strict Operational Constraints
* **Logic Preservation:** You must preserve 100% of the backend logic, APIs, routes, Jinja loops, and JavaScript dependencies. 
* **DOM Integrity:** Do NOT change the `id` attributes of any HTML elements, inputs, buttons, or form structures. The massive 4700-line `case.html` relies heavily on exact `id` lookups and data attributes.
* **Component Restructuring:** You *may* and *should* change DOM hierarchy, wrapping `div`s, layout grids, and CSS classes to achieve the new design, so long as the JS hooks remain intact.

---

## 2. Global Visual Identity

### Aesthetic Philosophy
* **Minimalist & Dense:** Information density should be high but visually uncluttered, typical of pro-tools (IDE-like).
* **Borders over Backgrounds:** Rely on extremely subtle borders (`1px solid rgba(0,0,0,0.06)` or `var(--color-slate-200)`) to separate sections rather than heavy background colors.
* **Depth via Shadows:** Use layered, diffuse shadows to establish elevation (e.g., floating command bars, modal popovers).
* **Typography-Led:** Hierarchy is established through typography weight, size, and color (slate-900 vs slate-500), not just layout.

### Design Tokens (To overwrite `design-tokens.css`)
* **Color Palette:** Move to a refined Slate (Grayscale) and Sky (Accent) palette. 
  * `Surface`: `#ffffff`
  * `Background`: `#fafafa`
  * `Borders`: `#e5e7eb`
  * `Text Primary`: `#111827`
  * `Text Secondary`: `#6b7280`
  * `Accent/Brand`: `#000000` (Linear style) or a vibrant Vercel Blue `#0070f3`.
* **Typography:** 
  * Primary: `Inter`, `SF Pro Display`, system-ui.
  * Monospace: `Geist Mono`, `JetBrains Mono`.
  * Hindi/Devanagari: Ensure `Mangal` renders cleanly without disrupting vertical rhythm.
* **Border Radius:** Standardize on `6px` for small components (buttons, inputs) and `12px` for large containers (panels, modals).

---

## 3. Structural Layout Transformations

### A. The Application Shell (`shell.css`)
* **Current:** Standard 250px dark sidebar + top header.
* **New Vision:** A macOS/Linear inspired layout.
  * **Sidebar:** Translucent background (glassmorphism), very thin borders, pills for navigation items instead of full-width blocks. Only icons and short labels. Collapsible to 60px.
  * **Header:** Merge breadcrumbs and global actions into a slim, 48px top bar with a bottom border.
  * **Main Content Area:** Edge-to-edge canvas with inner padded containers.

### B. Dashboard (`dashboard.html`)
* **KPI Strip:** Remove the heavy "cards". Transform into a seamless horizontal ticker or a clean grid of values with sparklines or subtle trend indicators.
* **Filter Bar:** Turn into a Mac-like command bar (rounded, floating appearance, flex-row) integrated directly above the data grid.
* **Data Table:** 
  * Borderless rows.
  * Sticky header with a subtle translucent blur.
  * Avatars/Icons for Doc Types instead of chunky badges.
  * Status badges become small filled dots with accompanying text.

### C. Case Workspace (`case.html`) - The Heavy Lift
This file is an enormous 4700-line SPA. It requires an IDE-like layout transformation.
* **Current Layout:** 30% Left Panel (Config/Upload), 70% Right Panel (Tabs: Entities / Title Chain).
* **New Vision (The "Inspector" Pattern):**
  * **Left Pane (Context/Settings):** 250px fixed column containing Document Mode, Bank selection, AI Config, and File Upload Dropzones. This should look like a Vercel project settings sidebar.
  * **Center Pane (Main Editor):** The Verification Form. 
    * Shift from standard vertical Bootstrap forms to a **Property Inspector Layout** (Label on the left, Input aligned on the right).
    * Bilingual fields (English/Hindi) should be side-by-side inside seamless, unified input groups, not separate bulky columns.
  * **Right/Bottom Pane (Title Chain):** The Timeline should act like a Git commit history or a linear step-tracker, with sleek connecting lines and dot indicators. The split editor/preview should resemble a split code editor (VS Code style).

### D. Template Builder (`template_builder.html`)
* **Bug Fix Requisite:** The file has a broken DOM structure. A `</script>` tag is missing before `</main>` at line 511. Fix this during restructuring.
* **Layout:** Convert to a 3-pane view. Left: Field Catalog (Sidebar). Center: Document Text / Mapping workspace. Right: Unmapped Text / Report.

### E. DevLys Converter (`devlys_to_unicode.html`)
* **Bug Fix Requisite:** The file is heavily corrupted with a duplicate overlapping DOM structure (lines 1-271 abruptly jump into a duplicate block from line 272-688). Strip out the duplication so it is a single valid HTML document.
* **Layout:** Treat this as an isolated "Utility Modal". It should be a beautifully centered, floating card with a massive, inviting drag-and-drop zone. No unnecessary page wrapper elements.

---

## 4. Component Re-engineering (`components.css`)

* **Inputs & Selects:** Remove heavy borders. Use a light background `#f4f4f5` that deepens on hover, or a strict minimalist `border-bottom` only. Focus states should use a subtle, crisp ring (e.g., `box-shadow: 0 0 0 2px rgba(0,0,0,0.8)`).
* **Hindi Legacy Inputs (`.hindi-legacy-input`):** Keep the soft yellow indication but make it highly sophisticated (e.g., `background: #fdfdf5`, `border: 1px solid #eab308`).
* **Buttons:**
  * Primary: High contrast (Black or deep Slate) with white text, slight shadow.
  * Secondary: Transparent with a 1px border.
  * Danger: Soft red background `#fef2f2` with dark red text `#991b1b`.
* **Drag-and-Drop Zones:** Instead of basic dashed borders, use a soft background with a centralized icon layout that pulses gently via CSS animations on dragover.
* **GSAP Micro-interactions:** Add subtle layout shifts. For example, when a new Title Chain card is added, it should expand smoothly. Tab transitions should crossfade and slide up by 4px.

---

## 5. Execution Phasing Strategy

To prevent breaking the massive JS dependency web, the implementing agent MUST proceed in this exact order:

1. **Phase 1: File Fixes & Cleanup**
   * Fix the corrupted HTML in `devlys_to_unicode.html`.
   * Fix the missing script tags in `template_builder.html`.
2. **Phase 2: The Core Tokens & Shell**
   * Completely rewrite `design-tokens.css`, `base.css`, and `shell.css`.
   * Apply the new Sidebar and Header layouts to all 4 HTML templates.
3. **Phase 3: Component Library**
   * Rewrite `components.css`. Strip all bulky Bootstrap appearances and apply the sleek, Linear/Vercel styling to inputs, buttons, tables, and cards.
4. **Phase 4: Dashboard Page Refactor**
   * Restructure the `dashboard.html` HTML grid to match the new Data Grid and KPI layout.
5. **Phase 5: Case Workspace Refactor**
   * Carefully restructure `case.html`. Break the forms out of standard Bootstrap cards and into the new "Inspector" layout. Verify that all JS-bound IDs remain intact.
6. **Phase 6: Micro-interactions & Final Polish**
   * Update the inline GSAP script blocks to match the new element classes and provide smooth, high-fps entrance and state-change animations.
