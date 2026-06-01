import docx
import sys

sys.stdout.reconfigure(encoding='utf-8')
doc = docx.Document("templates/SALE_DEED/SD_JDA_2SD_Flat_2S_1B.docx")

print("--- TABLES IN DOCUMENT ---")
for idx, t in enumerate(doc.tables):
    print(f"\nTable {idx}: {len(t.rows)} rows, {len(t.columns)} cols")
    for r_idx, row in enumerate(t.rows):
        cells_text = [cell.text.strip().replace("\n", " ") for cell in row.cells]
        print(f"  Row {r_idx}: {cells_text[:4]}")
