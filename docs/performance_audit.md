# RM-Maker Performance Audit & Optimization Plan

This document identifies major performance bottlenecks in the RM-Maker application and outlines concrete optimization strategies to improve response times, reduce API token usage, and enhance codebase scalability.

---

## 1. Synchronous Disk I/O & Case Loading Bottleneck ($O(N)$ Scaling)

### The Bottleneck
- **Location:** `app.py:154-162` (`list_cases()`)
- **Impact:** High page-load times on the dashboard (`/`) and API routes.
- **Detail:**
  ```python
  def list_cases():
      cases = []
      if not os.path.exists(CASES_DIR): return []
      for d in os.listdir(CASES_DIR):
          path = os.path.join(CASES_DIR, d, "session.json")
          try:
              with open(path, "r") as f: cases.append(json.load(f))
          except: pass
      return sorted(cases, key=lambda x: x.get("last_updated", 0), reverse=True)
  ```
  Every request to `/` (dashboard) and `/api/cases/recent` iterates over the entire `cases/` directory, opening, reading, and parsing `session.json` for every single case on the disk. As case counts grow:
  - Disk I/O scales linearly $O(N)$.
  - Synchronous execution blocks the single-threaded Flask server for other users.
  - CPU spends time recursively running `convert_hindi_digits_to_english` on load.

### Optimization Plan
1. **SQLite Database Migration:**
   - Migrate session management from file-based JSON to a local SQLite database using SQLAlchemy.
   - Store metadata (e.g., `id`, `last_updated`, `doc_type`, client names) in dedicated indexed columns.
   - Store the rich JSON data blob in a `TEXT` or `JSON` database column.
   - Rewrite the dashboard and API routes to use SQL pagination (`LIMIT` / `OFFSET`) and only load necessary fields, reducing load complexity from $O(N)$ disk reads to $O(1)$ database queries.
2. **Short-Term Memory Caching:**
   - Cache case listing results globally in-memory and invalidate the cache only when cases are created, modified, or deleted.

---

## 2. Gemini API PDF Binary Payload Overhead

### The Bottleneck
- **Location:** `modules/rm/extractor.py:103-112` and `modules/sd/extractor.py:590-607`
- **Impact:** Extreme latency (up to 40+ seconds per prompt), high token consumption, and increased Gemini API cost.
- **Detail:**
  - In Registered Mortgage (RM) extraction mode, full binary PDF files (often 10–50 pages of legal reports and title deeds) are read as bytes and sent directly in the payload to Gemini:
    ```python
    with open(path, 'rb') as f:
        raw = f.read()
    contents.append(types.Part.from_bytes(data=raw, mime_type=mime_type))
    ```
  - In Sale Deed (SD) extraction mode, while the dedicated `/extract_chain` route uses text-prefiltering (`_filter_relevant_pages`), the main multi-bucket extraction endpoint (`extract_buckets_with_ai`) still uploads the full raw PDF bytes for the `legal` bucket.

### Optimization Plan
1. **Enable PDF Text-Pre-filtering in RM Mode:**
   - Port the keyword-based page filtering logic from `SDDataExtractor` to `RMDataExtractor`.
   - Read the searchable text of the PDF first. If the PDF contains text, filter and compile only the relevant pages (e.g., pages mentioning interest rates, loan terms, properties, names) to send as lightweight text parts rather than the full binary.
2. **Apply Pre-filtering to SD Legal Bucket:**
   - Update `SDDataExtractor._run_gemini_extraction` to check for text-searchable PDFs and apply `_filter_relevant_pages` on the `legal` bucket files before sending the payload.

---

## 3. Redundant Template Discovery

### The Bottleneck
- **Location:** `app.py:75-149` (`discover_templates()`)
- **Impact:** CPU/disk overhead on template compilation and case viewing.
- **Detail:**
  `discover_templates()` is called on every request to `/case/<case_id>` and `/case/<case_id>/generate`. It runs filesystem scans (`os.listdir`) and parses regular expressions on filenames to reconstruct the template mapping dictionaries.

### Optimization Plan
- Cache the output of `discover_templates` globally or use `functools.lru_cache()`.
- Clear/invalidate the cache only when custom templates are uploaded (`/upload_custom_template`) or cleared (`/clear_custom_template`).

---

## 4. CPU-Bound Sequential Word Formatting & Run Processing

### The Bottleneck
- **Location:** `modules/sd/processor.py:417-434` and `modules/sd/processor.py:564-672`
- **Impact:** High document compilation latency, CPU saturation.
- **Detail:**
  After template rendering, the processor re-traverses the entire Document structure run-by-run to apply custom highlight styling, font overrides (`DevLys 040` vs. `Arial`), and spacing/ligature cleanups.
  This run-by-run manipulation is CPU-heavy and operates sequentially:
  ```python
  for paragraph in doc.paragraphs:
      self._highlight_paragraph_robust(paragraph, highlight_ai, highlight_missing)
      self._apply_mixed_fonts_to_paragraph(paragraph)
  ```

### Optimization Plan
- **Pre-Compile Run Mappings:** Cache the detection of DevLys mappings and avoid processing paragraphs/runs that do not contain Hindi characters or variables.
- **Vectorized/Batch XML Processing:** Instead of parsing and mutating the python-docx structures on run-level, operate directly on the underlying XML tree (`paragraph._p.xml`) using regular expressions where applicable to perform bulk font mappings and cleanups in C-speed.

---

## 5. Synchronous Transliteration Network Calls

### The Bottleneck
- **Location:** `app.py:2105-2200` (`/transliterate`)
- **Impact:** Input lag in the browser UI during field editing.
- **Detail:**
  The transliteration service makes synchronous HTTP calls to Google's inputtools endpoint for each word on blur/tab events.

### Optimization Plan
- Implement a simple local SQLite cache or memory cache (`transliteration_cache`) mapping common English legal names/addresses to their Hindi equivalents, avoiding the network roundtrip entirely for repeated terms.
