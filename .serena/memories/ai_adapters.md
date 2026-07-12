# AI Provider Adapters Memory

This system primarily integrates with the Google Gemini API to extract structured fields and generate chain-of-title narratives.

## Gemini SDK Client
- Initialized via `google-genai` SDK: `genai.Client(api_key=key)`.
- Models: `gemini-2.5-flash` for fast parsing, `gemini-2.5-pro` for deep reasoning.

## API Key Rotation & Failover
- Extractor classes (`RMDataExtractor`, `SDDataExtractor`) accept a list of API keys (`DEFAULT_GEMINI_API_KEYS` from `utils/config.py`).
- If an extraction call fails due to `APIError`, rate limiting, or connection issues:
  - It triggers `_rotate_key()` to switch to the next key.
  - Retries the operation up to `len(api_keys)` times.
  - Implements exponential backoff using `tenacity` retry wrappers.

## Hybrid PDF Page Pre-Filtering
- **Problem**: Large deed files (e.g. scanned PDFs) contain many repetitive legal pages, costing excess tokens and causing LLM attention drift.
- **Solution**: `select_relevant_pdf_pages(pdf_path, keywords)` pre-filters PDF pages:
  - Always includes the **first two pages** and the **last page** (contain dates, party info, execution blocks).
  - Inspects middle pages and selects those matching key legal terms (e.g. *boundaries, khasra, plot, covenant, loan, witness*).
  - Caps the selection at a maximum of **12 pages** total.
  - Searchable PDFs send selected page text; scanned PDFs fall back to sending full file bytes for vision models.

## Provider Adapters Documentation
- Configuration specifications for alternative LLMs are documented in:
  - [GEMINI.md](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/adapters/GEMINI.md)
  - [CLAUDE.md](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/adapters/CLAUDE.md)
  - [GPT_OSS.md](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/adapters/GPT_OSS.md)
