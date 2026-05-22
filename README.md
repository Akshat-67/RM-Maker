# LegalDoc Automator (v3)

An automated Registered Mortgage (RM) generation system for law firms.

## Workflow
1. **Choose Settings:** Select the Bank, number of borrowers, and number of loans.
2. **Dump Documents:** Add all photos (JPG/PNG) or PDFs of source documents at once.
3. **Automate:** Click "START AUTOMATION". The tool performs OCR and extraction via Gemini AI.
4. **Verify:** Check the extracted data on the right panel and edit any fields.
5. **Generate:** Click "GENERATE FINAL RM DOCX". The app automatically uses the correct Master Template based on your settings.

## Folder Structure
- `templates/`: Contains the Master .docx files with short-tags.
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
