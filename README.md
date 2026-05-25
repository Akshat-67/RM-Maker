# LegalDoc Automator (v3)

An automated Registered Mortgage (RM) generation system for law firms.

## Workflow
1. **Choose Settings:** Select the Bank, number of borrowers, and number of loans.
2. **Choose Template:** Let the app auto-pick from `templates/`, or upload your own `.docx` containing placeholders such as `{{bs[0].n}}`, `{{ls[0].a}}`, and `{{ws[0].n}}`.
3. **Dump Documents:** Add all photos (JPG/PNG) or PDFs of source documents at once.
4. **Guide AI:** Optionally type known borrower/witness names. This is useful when signatures or witness sections could confuse extraction.
5. **Automate:** Click "START AUTOMATION". The tool performs OCR and extraction via Gemini AI.
6. **Verify:** Check the extracted data on the right panel and edit any fields.
7. **Generate:** Click "GENERATE FINAL RM DOCX". The app fills the selected template and safely leaves missing indexed fields blank instead of crashing.

## Formatting
The final RM keeps the static formatting from the selected Word template. Inserted values inherit the formatting applied to their placeholders, so place each placeholder exactly where the variable text belongs and style the placeholder with the required font, size, bold, underline, etc.

## Folder Structure
- `templates/`: Contains the Master .docx files with short-tags/placeholders.
- `template_tools/`: Contains `template_builder.py` to create new Master Templates for other banks.
- `app.py`: The main desktop application.

## Installation
1. Install Python 3.10+ (Check "Add to PATH").
2. Run: `pip install -r requirements.txt`
3. Run: `python app.py`

## Adding New Banks (e.g., Piramal)
1. Run `python template_tools/template_builder.py`.
2. Follow the 'Audit -> Approve -> Tag' workflow to create a new Master Template.
3. Place the new file in the `templates/` folder.
4. (Optional) Update the `self.template_map` in `app.py` to include the new bank.
