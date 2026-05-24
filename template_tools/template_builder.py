import os
import sys
import json
import re
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from docx import Document

# Add root directory to path so extractor can be found
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from extractor import DataExtractor

class TemplateBuilder:
    def __init__(self, root):
        self.root = root
        self.root.title("LegalDoc Template Builder (Expert Mode)")
        self.root.geometry("1000x900")

        self.doc_path = ""
        self.mapping = {}
        self.setup_ui()

    def setup_ui(self):
        # Header
        header = tk.Frame(self.root, bg="#34A853", height=50); header.pack(fill="x")
        tk.Label(header, text="Expert Mode: Create Master Templates", fg="white", bg="#34A853", font=("Segoe UI", 12, "bold"), padx=10, pady=10).pack(side="left")

        # Instructions
        tk.Label(self.root, text="Step 1: Select a manually finished RM document to use as a source.", fg="grey").pack(pady=5)

        # File Selection
        f = tk.Frame(self.root, padx=10); f.pack(fill="x")
        tk.Button(f, text="Select Source RM (.docx)", command=self.load_doc, width=25).pack(side="left")
        self.path_lbl = tk.Label(f, text="No file selected", fg="blue"); self.path_lbl.pack(side="left", padx=10)

        # AI Configuration
        tk.Label(self.root, text="\nStep 2: Connect AI to discover data fields.", fg="grey").pack()
        api_f = tk.Frame(self.root, padx=10, pady=10, bg="#F1F3F4"); api_f.pack(fill="x", padx=10)

        tk.Label(api_f, text="API Key:", bg="#F1F3F4").grid(row=0, column=0, sticky="w")
        self.api_key_entry = tk.Entry(api_f, width=40, show="*"); self.api_key_entry.grid(row=0, column=1, padx=5)

        tk.Label(api_f, text="AI Model:", bg="#F1F3F4").grid(row=1, column=0, sticky="w", pady=(5,0))
        self.model_var = tk.StringVar(value="gemini-1.5-flash")
        self.model_dropdown = ttk.Combobox(api_f, textvariable=self.model_var, values=["gemini-1.5-flash"])
        self.model_dropdown.grid(row=1, column=1, sticky="ew", padx=5, pady=(5,0))

        tk.Button(api_f, text="Verify Key & Get Models", command=self.refresh_models).grid(row=0, column=2, rowspan=2, padx=10)

        tk.Button(self.root, text="🔍 RUN DATA DISCOVERY (AI)", command=self.discover_data, bg="#34A853", fg="white", font=("Arial", 11, "bold"), pady=10).pack(pady=15)

        # Mapping Table
        tk.Label(self.root, text="Step 3: Verify and Edit the identified strings:", font=("Arial", 10, "bold")).pack()
        self.tree = ttk.Treeview(self.root, columns=("Raw String", "Tag"), show='headings', height=15)
        self.tree.heading("Raw String", text="Exact Text in Document")
        self.tree.heading("Tag", text="Assigned Tag (e.g. {{bs[0].n}})")
        self.tree.column("Raw String", width=650)
        self.tree.column("Tag", width=250)
        self.tree.pack(fill="both", expand=True, padx=10)

        # Bottom Buttons
        btn_f = tk.Frame(self.root, pady=20); btn_f.pack()
        tk.Button(btn_f, text="SAVE MASTER TEMPLATE", command=self.generate_master, bg="#1A73E8", fg="white", font=("Arial", 12, "bold"), padx=30, pady=10).pack()

    def load_doc(self):
        p = filedialog.askopenfilename(filetypes=[("Word", "*.docx")])
        if p: self.doc_path = p; self.path_lbl.config(text=os.path.basename(p))

    def refresh_models(self):
        k = self.api_key_entry.get()
        if not k: messagebox.showwarning("Key Required", "Paste API Key first."); return
        try:
            extractor = DataExtractor(k)
            models = extractor.get_available_models()
            if models:
                self.model_dropdown['values'] = models
                self.model_var.set(models[0])
                messagebox.showinfo("Success", f"Found {len(models)} models!")
            else: messagebox.showerror("No Models", "Check your key settings.")
        except Exception as e: messagebox.showerror("Error", str(e))

    def discover_data(self):
        if not self.doc_path: messagebox.showwarning("File?", "Select source RM doc first"); return
        key, model_name = self.api_key_entry.get(), self.model_var.get()
        if not key: messagebox.showerror("Error", "Need API Key"); return

        doc = Document(self.doc_path)
        content_parts = []
        for p in doc.paragraphs:
            if p.text.strip(): content_parts.append(p.text)
        for table in doc.tables:
            for row in table.rows:
                content_parts.append(" | ".join(cell.text.strip() for cell in row.cells))
        raw_content = "\n".join(content_parts)

        prompt = f"""
        Analyze this Registered Mortgage (RM) document text.
        Your goal is to transform it into a 'Master Template' by identifying ALL variable data and replacing it with system tags.

        SYSTEM TAG SCHEMA (Core Fields):
        - Borrowers (bs): {{{{bs[i].s}}}} (Salutation), {{{{bs[i].n}}}} (Name), {{{{bs[i].a}}}} (Age), {{{{bs[i].r}}}} (Relation S/o, W/o), {{{{bs[i].rn}}}} (Relative Name), {{{{bs[i].adr}}}} (Address)
        - Loans (ls): {{{{ls[i].n}}}} (LAN No), {{{{ls[i].a}}}} (Amount value), {{{{ls[i].w}}}} (Amount in words), {{{{ls[i].t}}}} (Tenure/Period)
        - Properties (ps): {{{{ps[i].adr}}}} (Address), {{{{ps[i].n}}}} (North), {{{{ps[i].s}}}} (South), {{{{ps[i].e}}}} (East), {{{{ps[i].w}}}} (West)
        - Bank Signatory (bsign): {{{{bsign.n}}}} (Name), {{{{bsign.r}}}} (S/o, W/o), {{{{bsign.rn}}}} (Relative Name)
        - Dates: {{{{rd}}}} (RM Execution Date), {{{{ad}}}} (Loan Agreement Date)
        - Witnesses (ws): {{{{ws[i].n}}}} (Name), {{{{ws[i].r}}}} (S/o, W/o), {{{{ws[i].rn}}}} (Relative Name), {{{{ws[i].adr}}}} (Address)

        UNIVERSAL STRATEGY FOR TEMPLATE BUILDING:
        1. NO FRAGMENTS: Do not map small words like "Age", "Date", "S/o" alone. They will cause incorrect global replacements.
        2. CHUNKING: Replace the LARGEST logical block that contains the variable.
           Example: Instead of mapping "Jaipur", map "executed at Jaipur on this 5th day of May 2026" -> "executed at Jaipur on this {{{{rd}}}}".
           Example: Instead of "17,15,000/-", map "RS. 17,15,000/-" -> "RS. {{{{ls[0].a}}}}".
        3. OVER-COVERAGE: If you find a variable not in the core schema (like a Seller's name or a previous deed number), invent a logical tag like {{{{seller.n}}}} or {{{{prev_deed.no}}}}.
        4. REPETITION: Identify ALL occurrences of variables. If the same name appears in different parts, ensure it's mapped correctly.
        5. ACCURACY: The 'key' in your JSON must be the EXACT sub-string from the text below, including all symbols and spaces.

        Return ONLY a JSON dictionary: {{"EXACT STRING FROM TEXT": "TEXT WITH {{{{tags}}}}"}}
        Example: {{"RS. 12,00,000/-": "RS. {{{{ls[0].a}}}}", "executed by Mrs. Sharma": "executed by {{{{bs[0].s}}}} {{{{bs[0].n}}}}"}}

        TEXT TO ANALYZE:
        {raw_content}
        """

        try:
            extractor = DataExtractor(key)
            raw_response = extractor.raw_generate(prompt, model_name)
            if not raw_response:
                messagebox.showerror("AI Error", "No response from AI")
                return

            match = re.search(r'\{.*\}', raw_response, re.DOTALL)
            if match:
                self.mapping = json.loads(match.group(0))
                self.update_tree()
            else: messagebox.showerror("AI Error", f"Failed to parse JSON output. Raw: {raw_response[:200]}...")
        except Exception as e: messagebox.showerror("Error", str(e))

    def update_tree(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        for k, v in self.mapping.items(): self.tree.insert("", "end", values=(k, v))

    def generate_master(self):
        if not self.doc_path or not self.mapping: return
        doc = Document(self.doc_path)
        reps = sorted(self.mapping.items(), key=lambda x: len(x[0]), reverse=True)

        # Process all paragraphs in main body
        for p in doc.paragraphs:
            self.apply_reps(p, reps)

        # Process all tables
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for p in cell.paragraphs:
                        self.apply_reps(p, reps)

        # Process Headers and Footers
        for section in doc.sections:
            for hp in section.header.paragraphs: self.apply_reps(hp, reps)
            for fp in section.footer.paragraphs: self.apply_reps(fp, reps)

        save_p = filedialog.asksaveasfilename(defaultextension=".docx")
        if save_p: doc.save(save_p); messagebox.showinfo("Success", "Master Template Created!")

    def apply_reps(self, p, reps):
        if not p.text.strip(): return
        for old, new in reps:
            self.replace_text_preserving_format(p, old, new)

    def replace_text_preserving_format(self, paragraph, old_text, new_text):
        """Replaces text while trying to preserve run-level formatting, with extreme robustness."""
        if not old_text or old_text == new_text: return

        # 1. Normalize spaces in search string
        normalized_old = re.sub(r'\s+', ' ', old_text).strip()

        # 2. Create an extremely robust regex pattern
        # re.escape handles most special chars.
        # In Python 3.12+, re.escape might escape spaces as '\ '.
        pattern_str = re.escape(normalized_old)

        # 3. Handle spaces robustly: Replace escaped spaces or literal spaces with \s*
        pattern_str = pattern_str.replace(r'\ ', r'\s*').replace(' ', r'\s*')

        # 4. Allow optional space after common punctuation/symbols often split in Word runs
        # These are already escaped by re.escape, so we match the escaped versions
        for char in [r'\.', r'\/', r'\-', r'\,', r'\(', r'\)', r'\:', r'\\', r'\[', r'\]']:
            pattern_str = pattern_str.replace(char, char + r'\s*')

        try:
            # Multi-line and Dotall to handle text split in weird ways across runs
            pattern = re.compile(pattern_str, re.IGNORECASE | re.MULTILINE | re.DOTALL)
        except Exception:
            return

        # Use a limit to prevent infinite loops if something goes wrong
        max_reps = 100
        while max_reps > 0:
            max_reps -= 1
            full_text = "".join(r.text for r in paragraph.runs)
            match = pattern.search(full_text)
            if not match: break

            start_idx, end_idx = match.start(), match.end()

            cur_len = 0
            start_run_idx = -1
            end_run_idx = -1
            start_offset = -1
            end_offset = -1

            for i, run in enumerate(paragraph.runs):
                run_len = len(run.text)
                if start_run_idx == -1 and cur_len <= start_idx < cur_len + run_len:
                    start_run_idx = i
                    start_offset = start_idx - cur_len
                if cur_len < end_idx <= cur_len + run_len:
                    end_run_idx = i
                    end_offset = end_idx - cur_len
                    break
                cur_len += run_len

            if start_run_idx != -1 and end_run_idx != -1:
                if start_run_idx == end_run_idx:
                    r = paragraph.runs[start_run_idx]
                    r.text = r.text[:start_offset] + new_text + r.text[end_offset:]
                else:
                    paragraph.runs[start_run_idx].text = paragraph.runs[start_run_idx].text[:start_offset] + new_text
                    for i in range(start_run_idx + 1, end_run_idx):
                        paragraph.runs[i].text = ""
                    paragraph.runs[end_run_idx].text = paragraph.runs[end_run_idx].text[end_offset:]
            else:
                # Fallback to simple replace if run tracking fails (rare)
                text = paragraph.text
                paragraph.text = pattern.sub(new_text, text, count=1)
                break

if __name__ == "__main__":
    root = tk.Tk(); app = TemplateBuilder(root); root.mainloop()
