# Enterprise SaaS Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Completely redesign the application's user interface to meet the aesthetic standards of Linear, Vercel, Stripe, and Apple while preserving 100% of functional logic and dynamic JavaScript capabilities.

**Architecture:** We will replace the entire style layer of the app by rewriting the files under `static/css/`. Then, we will rewrite the HTML layouts in all four templates (`dashboard.html`, `devlys_to_unicode.html`, `template_builder.html`, and the massive `case.html`) to match a dense, IDE-like layout structure. All IDs, form elements, JS hooks, and Flask context variables are preserved exactly.

**Tech Stack:** HTML5, CSS Variables, Bootstrap 5 (only utilities/primitives, styling overridden), Vanilla JS (Sanscript, custom mapping), and GSAP for micro-animations.

## Global Constraints
* Do NOT modify the core extraction prompt, merging logic, relation splitting, or normalization helper functions in `modules/sd/extractor.py`, `modules/rm/extractor.py`, `modules/rm/schema.py`, or `utils/helpers.py`.
* Devanagari numerals (`०-९`) must always be converted to standard English digits (`0-9`) globally.
* The verification UI must present Hindi text in a clean Unicode Devanagari font (`Segoe UI` or `Mangal`). Legacy non-Unicode fonts (`DevLys 010` or `Kruti Dev`) must never be used to style inputs.
* Do NOT modify, disable, or alter the real-time English-to-Hindi transliteration workflow or `/transliterate` endpoints.
* Do NOT touch or modify the RM relation parsing or assignment workflows. Keep custom jinja filters and `unassigned_aadhars` logic intact.
* Preserving element `id`s and `onclick` bindings is critical. If any ID is changed, the JS event loops in `case.html` will break.

---

### Task 1: Template Integrity & File Fixes
**Files:**
- Modify: `web_templates/devlys_to_unicode.html` (resolve duplication)
- Modify: `web_templates/template_builder.html` (resolve missing script tag)

- [ ] **Step 1: Clean up corrupted duplicate block in devlys_to_unicode.html**
  Lines 1–271 of `web_templates/devlys_to_unicode.html` contain the correct beginning but cut off inside `alertContainer`. Lines 272–688 contain a duplicate copy of the CSS, HTML head, and body, but include the correct JavaScript block and closing tags. Re-stitch the file: keep lines 1–271, discard the duplicate CSS/HTML head block (lines 272–475), and append the correct closing container tags, scripts, and footer elements (lines 476–688).
- [ ] **Step 2: Fix missing script tag in template_builder.html**
  At line 511 of `web_templates/template_builder.html`, the `</main>` tag is placed inside the `<script>` tag because the script tag opened at line 198 is never closed. Insert `</script>` directly before line 511.
- [ ] **Step 3: Run app to verify template parsing succeeds**
  Run Flask development server if running locally, and browse `/devlys-to-unicode` and `/template-builder` to verify they load without syntax or rendering errors.
- [ ] **Step 4: Commit changes**
  ```bash
  git add web_templates/devlys_to_unicode.html web_templates/template_builder.html
  git commit -m "style: fix template structural errors and file corruption"
  ```

---

### Task 2: Core Design Tokens & Base CSS Overhaul
**Files:**
- Modify: `static/css/design-tokens.css`
- Modify: `static/css/base.css`

- [ ] **Step 1: Define Slate & Accent color variables in design-tokens.css**
  Replace `:root` declarations in `design-tokens.css` with a high-contrast dark theme or a refined professional light/dark system.
  ```css
  :root {
      --color-zinc-50: #fafafa;
      --color-zinc-100: #f4f4f5;
      --color-zinc-200: #e4e4e7;
      --color-zinc-300: #d4d4d8;
      --color-zinc-400: #a1a1aa;
      --color-zinc-500: #71717a;
      --color-zinc-700: #3f3f46;
      --color-zinc-800: #27272a;
      --color-zinc-900: #18181b;
      --color-zinc-950: #09090b;

      --color-blue-500: #3b82f6;
      --color-blue-600: #2563eb;
      --color-emerald-500: #10b981;
      --color-amber-500: #f59e0b;
      --color-rose-500: #ef4444;

      --theme-bg-page: var(--color-zinc-950);
      --theme-bg-surface: var(--color-zinc-900);
      --theme-border: var(--color-zinc-800);
      --theme-primary: var(--color-zinc-50);
      --theme-text-primary: var(--color-zinc-50);
      --theme-text-secondary: var(--color-zinc-400);
      --theme-text-muted: var(--color-zinc-500);
      --theme-accent: var(--color-blue-500);
      --theme-success: var(--color-emerald-500);
      --theme-warning: var(--color-amber-500);
      --theme-error: var(--color-rose-500);
  }
  ```
- [ ] **Step 2: Clean up layouts in base.css**
  Simplify flex/grid classes to support modern high-density layouts.
- [ ] **Step 3: Commit changes**
  ```bash
  git add static/css/design-tokens.css static/css/base.css
  git commit -m "style: establish premium zinc design tokens and layout baselines"
  ```

---

### Task 3: Component Styles & Application Shell
**Files:**
- Modify: `static/css/components.css`
- Modify: `static/css/shell.css`
- Modify: `static/style.css`

- [ ] **Step 1: Re-engineer shell.css**
  Implement a thin-border app shell layout.
  * Clean dark-mode app container with a 240px wide sidebar.
  * Change navigation links to minimal hover pills with clear active states (`background-color: var(--color-zinc-800)`).
  * Reduce header height to 48px, edge-to-edge layout, with subtle border separator.
- [ ] **Step 2: Re-engineer components.css**
  * **Buttons:** Minimalist high-contrast buttons (`.btn-primary` uses black/zinc-50 background, `.btn-secondary` uses thin borders).
  * **Inputs/Selects:** Light Zinc background inside inputs (`var(--color-zinc-900)`), changing border color to `var(--color-zinc-700)` on hover and `var(--theme-accent)` on focus. No heavy shadows.
  * **Tables:** Completely borderless table rows with a subtle transparent hover overlay (`rgba(255, 255, 255, 0.02)`).
  * **Hindi Inputs:** Clean light-yellow backing indicator (`rgba(245, 158, 11, 0.05)`) to guide transliteration fields cleanly.
- [ ] **Step 3: Overwrite style.css**
  Remove any legacy styling elements that conflict with the clean system.
- [ ] **Step 4: Commit changes**
  ```bash
  git add static/css/components.css static/css/shell.css static/style.css
  git commit -m "style: implement modern shell layout and minimalist component library"
  ```

---

### Task 4: Dashboard Transformation
**Files:**
- Modify: `web_templates/dashboard.html`

- [ ] **Step 1: Redesign Dashboard KPI Strip**
  Replace columns with a high-density, horizontal metrics strip. Replace bulk cards with minimal key-value blocks.
  ```html
  <div class="row g-3 mb-4">
    <!-- Total Cases -->
    <div class="col-md-4">
      <div class="p-3 rounded-lg border border-zinc-800 bg-zinc-900">
        <span class="text-xs text-zinc-500 uppercase tracking-wider">Total Active Cases</span>
        <div class="text-3xl font-bold mt-1 text-zinc-50">{{ cases|length }}</div>
      </div>
    </div>
  </div>
  ```
- [ ] **Step 2: Re-layout Search Toolbar**
  Integrate Search, Bank Filter, and Sort dropdowns into a floating command-style row.
- [ ] **Step 3: Revamp Cases Table**
  * Style the table header with `uppercase font-xs tracking-wider text-zinc-500`.
  * Replace the status badges with a minimal indicator dot (e.g., green dot for ready, yellow for pending) and plain-text status.
- [ ] **Step 4: Commit changes**
  ```bash
  git add web_templates/dashboard.html
  git commit -m "style: redesign case dashboard with developer console aesthetic"
  ```

---

### Task 5: DevLys Converter & Template Builder Redesign
**Files:**
- Modify: `web_templates/devlys_to_unicode.html`
- Modify: `web_templates/template_builder.html`

- [ ] **Step 1: Re-layout DevLys Converter**
  Convert the page to a focused tool card. Build a large drag-and-drop file upload zone styled like a pristine product landing page card (dashed border, glowing dragover animation).
- [ ] **Step 2: Re-layout Template Builder Workspace**
  Create a split 3-column builder workspace:
  * Left 3-cols: Field Catalog in a scrollable sidebar list.
  * Center 6-cols: Document Mappings table with clear confidence badges.
  * Right 3-cols: Unmapped/Raw ASCII preview panel.
- [ ] **Step 3: Commit changes**
  ```bash
  git add web_templates/devlys_to_unicode.html web_templates/template_builder.html
  git commit -m "style: overhaul builder and converter layout structures"
  ```

---

### Task 6: Case Workspace Layout Overhaul (case.html)
**Files:**
- Modify: `web_templates/case.html`

- [ ] **Step 1: Rearrange Main 2-Column Grid to 3-Pane Layout**
  Change the standard Bootstrap grid columns to create a balanced Workspace:
  * **Left Column (`col-lg-4 col-xl-3`):** Transform into a unified Settings Inspector containing Workspace Type details, Bank configuration, AI model selector, and File upload dropzones. Remove all individual card wrappers; present files as a clean list with delete actions.
  * **Right Column (`col-lg-8 col-xl-9`):** Dedicated entirely to Entity verification fields and the Title Chain interactive timeline.
- [ ] **Step 2: Re-engineer the Form Field Groups**
  Convert all verification cards (Sellers, Buyers, Borrowers, Loans, Property schedules) to an **Inspector Grid Layout**.
  * Use a two-column flex row for each field: Label on the left (20% width), Input fields on the right (80% width).
  * Align the English source fields and their Hindi transliterated targets side-by-side inside modern, slim borders. Keep inputs perfectly aligned.
  * **CRITICAL:** Do not change any of the HTML `id`s (like `field_sellers_{{loop.index0}}_n` etc.) or the `onclick` action listeners.
- [ ] **Step 3: Transform Title Chain Timeline Interface**
  * Create a horizontal timeline ticker `#chainTimeline` resembling a clean sequence map or interactive Git graph.
  * Re-arrange the Title Chain split container: Left pane is a structured editor card showing event properties; Right pane is a sticky preview pane showcasing the live-compiled Hindi narrative.
- [ ] **Step 4: Commit changes**
  ```bash
  git add web_templates/case.html
  git commit -m "style: major layout overhaul of the case workspace templates"
  ```

---

### Task 7: Micro-interactions & Final Verification
**Files:**
- Modify: `web_templates/case.html`
- Modify: `web_templates/dashboard.html`

- [ ] **Step 1: Refit GSAP animations**
  Update the inline animations script blocks to animate the new classes:
  * Dashboard load sequence: Metric blocks stagger slide-up, table rows fade-in.
  * Case timeline node activation: Use GSAP to scale active nodes and slide active link editor cards into view.
- [ ] **Step 2: Run verification test suite**
  Run full unit/integration tests to ensure no backend logic or APIs were broken during the DOM restructuring:
  `python -m pytest tests/`
- [ ] **Step 3: Commit changes**
  ```bash
  git add web_templates/case.html web_templates/dashboard.html
  git commit -m "style: refine micro-animations and verify redesign integrity"
  ```
