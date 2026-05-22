# LegalDoc Automator (v2)

A specialized tool for Law Firms to automate the generation of Registered Mortgage (RM) documents.

## Features
- **Integrated AI OCR:** Direct support for Images (JPG, PNG) and PDFs. Handles hand-scanned and blurry documents.
- **Short-Tag System:** Optimized tags to prevent breaking Word document formatting.
- **Verification UI:** Comprehensive editing screen for Borrowers, Loans, Properties, Witnesses, and Legal Documents.
- **Multi-Loan/Multi-Borrower:** Automatically handles complex cases with loops.

## Installation
1. Install Python 3.10+
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage
1. Run `python app.py`.
2. Add your source documents (Photos of Aadhar, PDF Sanction Letters, LSR).
3. Select a **Master Template** (Word document with tags).
4. Enter your Gemini API Key.
5. Click **Extract Data**, verify the results, and click **Generate**.

## Template Tagging
Refer to `template_tools/TAGS_REFERENCE.md` for the list of available tags.
Always use `docxtpl` (Jinja2) style tags:
- Simple: `{{rd}}`
- Loop: `{% for b in bs %}{{b.n}}{% endfor %}`

## Tools
- `template_tools/auto_tagger.py`: A helper script to help you create your first Master Template by replacing existing text with tags.
