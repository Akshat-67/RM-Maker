# DevLys 040 Template Compatibility Proof-of-Concept (POC)

## Goal
To determine if `docxtpl` (Jinja2 for Word) can safely identify and replace placeholders within a document where the text is styled with the legacy **DevLys 040** font.

## Methodology
1.  **Template Creation**: A `.docx` file was programmatically created with a paragraph styled in `DevLys 040`.
2.  **Placeholder Insertion**: Standard Jinja2 tags (`{{ name }}`, `{{ seller }}`, `{{ amount }}`) were inserted directly into the DevLys-styled text runs.
3.  **XML Inspection**: The underlying `word/document.xml` was extracted and analyzed to verify how placeholders and font styles are stored.
4.  **Data Injection**: `docxtpl` was used to render the template with a sample context.
5.  **Output Verification**: The resulting document was inspected to confirm successful substitution and font preservation.

## Findings

### 1. Placeholder Integrity
- **XML Representation**: Placeholders remain intact as plain ASCII text in the underlying XML.
  - *Example*: `<w:r><w:rPr><w:rFonts w:ascii="DevLys 040" .../></w:rPr><w:t>{{ name }}</w:t></w:r>`
- **Jinja Detection**: `docxtpl` successfully identified the placeholders because it operates on the XML string, ignoring the visual font mapping.

### 2. Visual Rendering Paradox
- **The "Gibberish" Effect**: Because DevLys 040 is a legacy font (mapping ASCII to Hindi glyphs), English characters like `{` and `}` render as Hindi characters (e.g., `{` becomes `क्ष`).
- **Human Readability**: A template purely in DevLys will be difficult for a human to verify visually in Word, as `{{ name }}` will appear as `क्षक्ष name द्वद्व`.
- **Injection Behavior**: When English text (e.g., "Praveen") is injected into a DevLys-styled run, it correctly renders as Hindi glyphs in Word.

### 3. Corruption Risks
- **Run Splitting**: Word occasionally splits text into multiple `<w:r>` tags (e.g., due to spellcheck or manual edits), which can break `docxtpl` detection.
- **Font Inheritance**: If a placeholder is inserted between two runs, it might inherit the document default font instead of DevLys, leading to inconsistent rendering in the final output.

## Technical Requirements for Implementation
1.  **Surgical Insertion**: The `TemplateBuilder` must ensure that placeholders are inserted into a single run to avoid breaking `docxtpl` detection.
2.  **Font Forcing**: During generation, the backend should ideally use `docxtpl.RichText` to explicitly force the `DevLys 040` font for injected text to ensure consistent appearance.
3.  **Visual Aids**: To assist human template designers, the `TemplateBuilder` could provide a "Preview Mode" that temporarily swaps DevLys for an English font (like Arial) to verify placeholder placement.

## Conclusion
**PROVEN COMPATIBLE.** `docxtpl` works perfectly with DevLys 040 templates because the underlying XML remains ASCII-compliant. The "corruption" observed by users is typically a visual rendering issue (Arial rendering ASCII meant for DevLys) rather than a data loss issue.

## Recommended Architecture
- **Storage**: Store verified data in **Unicode Hindi**.
- **Transformation**: At the point of document generation, convert Unicode Hindi to **DevLys ASCII**.
- **Injection**: Inject the DevLys ASCII into the template. The legacy font in the `.docx` will then render these characters as the correct Hindi glyphs.
- **Safety**: Use a "Surgical Replace" logic in the Template Builder to maintain XML run continuity.
