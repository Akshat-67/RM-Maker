# LegalDoc Automator Pro - Project Handoff

## 1. Project Overview & Architecture
LegalDoc Automator Pro is a specialized document generation and extraction platform tailored for Indian banking and legal workflows. It consists of two primary pipelines:
1. **Registered Mortgage (RM) Workflow**: Stable, production-ready pipeline that automates the creation of Registered Mortgage deeds.
2. **Sale Deed (SD) Workflow**: Extends the platform to handle sale deeds, featuring:
   - AI-assisted data extraction from Hindi and bilingual documents.
   - Dynamic seller, buyer, and witness card management in a responsive Web UI.
   - Live transliteration (English to Hindi) and DevLys 040 font previewing.
   - **Chain Engine**: Extracts and builds a chronological title history (`title_events[]`) from Title Search Reports (TSR), compiles them into a unified Hindi narrative block (`chain_text`), and formats them for final legacy Word output in DevLys 040 ASCII format.

### End-to-End SD Architecture
```
Legal Report (TSR)
      ↓
title_events[] (Extracted chronologically, reviewed/edited in UI)
      ↓
Review UI (Save/Edit dynamic rows)
      ↓
render_chain() (Python function generating Hindi prose)
      ↓
chain_text (Jinja2 string variable)
      ↓
SD Generation (Renders output DOCX, converting Unicode to DevLys 040)
```

---

## 2. Core Components & Schemas
- **[SD_SCHEMA.md](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/SD_SCHEMA.md)**: Shorthand data contract for Sale Deeds (e.g., `ss` for Sellers, `bs` for Buyers, `ps` for Properties, `reg` for Registration details). Stored in Unicode Hindi on the backend and converted to DevLys 040 for the output DOCX.
- **[CHAIN_SCHEMA.md](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/CHAIN_SCHEMA.md)**: Specifications for title history tracking. `title_events[]` contains details like `executant`, `claimant`, and `registration` (office, book, vol, page, etc.).
- **[CHAIN_EVENT_LIBRARY.md](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/CHAIN_EVENT_LIBRARY.md)**: Defines the legal text templates for generating narrative paragraphs for different event types (e.g., `ALLOTMENT`, `SALE_DEED`, `POA`, `RELINQUISHMENT`).
- **[CHAIN_WORKFLOW.md](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/CHAIN_WORKFLOW.md)**: Detailed technical description of the processing pipeline from TSR to final Word output.

---

## 3. The Source of Truth Rule
> [!IMPORTANT]
> **Actual generated DOCX output is the absolute source of truth.**
> Do not trust previous implementation reports, code inspections, or assumptions. Every regression and fix must be tested and verified by running the generation pipeline and inspecting the resulting document in Word to ensure layout, font rendering (Arial for Jinja tags, DevLys 040 for Hindi prose), and placeholder mappings are correct.

---

## 4. Current Challenge: Template Builder Regression
The Template Builder is designed to help operators convert a static, completed deed (.docx) into a reusable Master Template by running AI discovery to replace case-specific text with Jinja2 placeholders.

### The Conflict of Concerns
- **Template Builder Concerns**: Maximize editability, discovery, and field coverage. The master templates must be populated with granular, editable micro-placeholders (e.g., `{{ss[0].n}}`, `{{ps[0].village}}`, `{{title_chain[0].owner}}`, `{{reg.vol}}`) so that the template author is fully in control of the document structure.
- **Final SD Generation Concerns**: Dynamically compiles narrative blocks (such as `{{chain_text}}`, `{{ps[0].full_address}}`, `{{ps[0].dimension_text}}`, `{{ps[0].boundary_text}}`) from the database schema to render high-quality, automated prose.

### What Went Wrong
Recent changes mistakenly forced the Template Builder to prioritize final narrative blocks (`{{chain_text}}`, `{{ps[0].full_address}}`, etc.) during **AI Discovery** and template generation. Instead of discovering and tagging the individual fields, the builder started matching entire paragraphs and replacing them with a single block placeholder. 

**Resulting Regression:**
- Placeholder coverage dropped from **~95%** to **~78%**.
- Large sections of the document became static or un-editable.
- Mapped templates became significantly less useful because the author could no longer edit granular details in the builder interface.

---

## 5. Recovery Objective
Restore the Template Builder back to its original high-coverage state (~95% coverage) by:
1. Re-prioritizing the discovery and mapping of granular micro-placeholders.
2. Understanding which narrative-block logic belongs exclusively to the final document generation pipeline and should be removed/customized in the Template Builder.
3. Keeping the template builder safe, robust, and fully compatible with the core SD schema.
