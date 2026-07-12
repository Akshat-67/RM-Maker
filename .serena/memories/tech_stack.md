# Tech Stack Memory

This project uses a hybrid Python + JavaScript/HTML technology stack designed for AI document processing and browser automation on Windows.

## Backend Stack
- **Python Version**: 3.10+
- **Core Framework**: **Flask** (routing, static files, template loading).
- **CORS**: `Flask-CORS` for cross-origin extension requests.
- **Word Document Templates**: `docxtpl` (wrapping `python-docx`) for Jinja-like tag parsing in `.docx`.
- **Image Processing**: `Pillow` (PIL) for image-based Aadhaar/PAN handling.
- **PDF Extraction**: `pypdf` for parsing searchable text and page selection.
- **Environment variables**: `python-dotenv`.

## AI Integration
- **Client**: `google-genai` SDK (`genai.Client`).
- **Models**: `gemini-2.5-flash` (standard high-volume extraction, translation, narrative generation) and `gemini-2.5-pro` (complex reasoning).
- **Error Handling**: `tenacity` retry/backoff wrappers for API calls.
- **Provider Alternatives**: Configuration adapters for OpenAI and Claude (`adapters/`).

## Frontend UI
- **Framework**: Semantic HTML5 with **Vite/Vanilla JS** logic.
- **Styling**: **TailwindCSS (v4)** compiled via the Tailwind CLI.
- **Transliteration**: Local `Sanscript` fallback coupled with `/transliterate` API.
- **Font Rendering**: Unicode Devanagari (`Segoe UI`, `Mangal`) for Hindi inputs.

## e-Panjiyan Autofill extensions
- **Platform**: Chrome Extension (Manifest V3).
- **Languages**: HTML/CSS/JS (vanilla DOM injection, message passing between popup.js and content.js).

## Legacy Font Converter Tool
- **Platform**: Node.js v18 (CommonJS).
- **Packaging**: `pkg` compilation tool to build `devlys-clipboard-converter.exe` for Windows environments.
