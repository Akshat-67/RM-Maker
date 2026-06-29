# Raw Deeds Ingestion Folder (`Reference Materials/raw_deeds/`)

Drop your deed files or paragraph examples in this folder to feed them into the Title Chain Auto-Discovery and Parameterization Pipeline.

### Supported Formats
1. **Word Documents (`.docx`)**: Drop full sale deeds, patta documents, or inheritance deeds. The script will automatically parse them and isolate title chain paragraphs.
2. **Text Files (`.txt`)**: If you have already copied-and-pasted specific historical title chain paragraphs, you can save them in plain text files in this folder (one paragraph per file, or separated by double newlines).

### How to Run Discovery
Once you have placed your files in this folder, run the following command in your terminal:
```powershell
python scripts/discover_templates.py
```

The script will:
* Scan all files in this folder.
* Isolate historical ownership paragraphs.
* Use Gemini to parameterize names, dates, amounts, and registration details.
* Group and de-duplicate the resulting templates.
* Append all new variations directly to the app's database (`custom_chain_templates.json`), making them instantly active in the visual UI editor and backend narrative compiler.
