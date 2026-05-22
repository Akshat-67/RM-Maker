# LegalDoc Automator

A tool for law firms to automate the generation of Registered Mortgage (RM) documents from OCR text.

## Features
- **Data Extraction:** Uses AI (Gemini 1.5 Flash) to extract borrower info, loan details, and document lists from messy OCR text.
- **Verification Screen:** Allows users to review and edit extracted data before document generation.
- **Template Generation:** Uses Word templates with `{{tag}}` placeholders to create final documents.

## Setup
1. **Install Python:** Ensure you have Python 3.10+ installed.
2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Get a Gemini API Key:**
   - Go to [Google AI Studio](https://aistudio.google.com/) and create a free API key.

## Usage
1. Run the application:
   ```bash
   python app.py
   ```
2. **Select OCR Files:** Upload the `.txt` files containing OCR'd data from Aadhar cards, sanction letters, etc.
3. **Select Template:** Select your `.docx` bank template.
4. **Enter API Key:** Paste your Gemini API key.
5. **Extract:** Click "Extract Data".
6. **Verify:** Check the data in the verification screen, edit as needed.
7. **Generate:** Click "Generate Final RM Document" to save the result.

## Template Guide
Use the following tags in your Word documents:
- `{{borrower_1_name}}`, `{{borrower_1_age}}`, `{{borrower_1_address}}`
- `{{loan_acc_no}}`, `{{loan_amount}}`, `{{loan_amount_words}}`, `{{sanction_date}}`
- In the "Second Schedule", use a loop for documents:
  ```
  {% for doc in documents_list %}
  {{doc.text}}
  {% endfor %}
  ```
