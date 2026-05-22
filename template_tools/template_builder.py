import os
import json
import re
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from docx import Document
import google.generativeai as genai

class TemplateBuilder:
    def __init__(self, root):
        self.root = root
        self.root.title("LegalDoc Template Builder (Expert Mode)")
        self.root.geometry("1000x800")

        self.doc_path = ""
        self.mapping = {}
        self.setup_ui()

    def setup_ui(self):
        # Instructions
        instr = "1. Select a completed RM Doc (Source) -> 2. AI finds data -> 3. You verify strings -> 4. Script creates Master Template."
        tk.Label(self.root, text=instr, fg="grey", font=("Arial", 9, "italic")).pack(pady=5)

        # File Selection
        f = tk.Frame(self.root); f.pack(fill="x", padx=10)
        tk.Button(f, text="Select Source RM (.docx)", command=self.load_doc).pack(side="left")
        self.path_lbl = tk.Label(f, text="No file selected", fg="blue"); self.path_lbl.pack(side="left", padx=10)

        # API Key
        api_f = tk.Frame(self.root); api_f.pack(fill="x", padx=10, pady=5)
        tk.Label(api_f, text="Gemini API Key:").pack(side="left")
        self.api_key_entry = tk.Entry(api_f, width=40, show="*"); self.api_key_entry.pack(side="left")
        tk.Button(api_f, text="Run Data Discovery (AI)", command=self.discover_data, bg="green", fg="white").pack(side="left", padx=10)

        # Mapping Table
        tk.Label(self.root, text="Step 3: Verify literal strings exactly as found in Word:", font=("Arial", 10, "bold")).pack(pady=5)

        self.tree = ttk.Treeview(self.root, columns=("Raw String", "Tag"), show='headings', height=20)
        self.tree.heading("Raw String", text="Raw String (from Doc)")
        self.tree.heading("Tag", text="Assigned Tag")
        self.tree.column("Raw String", width=700)
        self.tree.column("Tag", width=200)
        self.tree.pack(fill="both", expand=True, padx=10)

        # Bottom Buttons
        btn_f = tk.Frame(self.root); btn_f.pack(pady=20)
        tk.Button(btn_f, text="Save Verified Mapping", command=self.save_mapping).pack(side="left", padx=5)
        tk.Button(btn_f, text="GENERATE MASTER TEMPLATE", command=self.generate_master, bg="blue", fg="white", font=("Arial", 11, "bold")).pack(side="left", padx=5)

    def load_doc(self):
        p = filedialog.askopenfilename(filetypes=[("Word", "*.docx")])
        if p: self.doc_path = p; self.path_lbl.config(text=os.path.basename(p))

    def discover_data(self):
        if not self.doc_path: return
        key = self.api_key_entry.get()
        if not key: messagebox.showerror("Error", "Need API Key"); return

        genai.configure(api_key=key)
        model = genai.GenerativeModel('gemini-1.5-flash')

        # Extract all text including tables
        doc = Document(self.doc_path)
        full_text = []
        for p in doc.paragraphs: full_text.append(p.text)
        for t in doc.tables:
            for r in t.rows:
                for c in r.cells: full_text.append(c.text)

        raw_content = "\n".join(full_text)

        prompt = f"""
        Analyze this Registered Mortgage text. Identify every variable piece of data (Names, Dates, Amounts, Addresses, LANs, Boundaries, Ages).

        CRITICAL: Provide the EXACT string as it appears in the text, including special dashes (–), tabs (\\t), or typos.

        Return a JSON dictionary where KEY is the EXACT RAW STRING and VALUE is the suggested tag.
        Example: {{"Mr. Anand Singh": "{{{{bs[0].n}}}}", "24th day March 2026": "{{{{rd}}}}"}}

        TEXT:
        {raw_content}
        """

        try:
            response = model.generate_content(prompt)
            match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if match:
                self.mapping = json.loads(match.group(0))
                self.update_tree()
            else:
                messagebox.showerror("AI Error", "Failed to parse AI output")
        except Exception as e: messagebox.showerror("Error", str(e))

    def update_tree(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        for k, v in self.mapping.items():
            self.tree.insert("", "end", values=(k, v))

    def save_mapping(self):
        save_p = filedialog.asksaveasfilename(defaultextension=".json")
        if save_p:
            with open(save_p, 'w') as f: json.dump(self.mapping, f, indent=2)

    def generate_master(self):
        if not self.doc_path or not self.mapping: return

        doc = Document(self.doc_path)
        # Sort replacements by length descending
        reps = sorted(self.mapping.items(), key=lambda x: len(x[0]), reverse=True)

        for p in doc.paragraphs:
            if not p.text.strip(): continue
            for old, new in reps:
                if old in p.text:
                    # Robust replacement: Merge runs first
                    text = p.text
                    p.text = text.replace(old, new)

        for t in doc.tables:
            for r in t.rows:
                for c in r.cells:
                    for p in c.paragraphs:
                        for old, new in reps:
                            if old in p.text:
                                p.text = p.text.replace(old, new)

        save_p = filedialog.asksaveasfilename(defaultextension=".docx")
        if save_p: doc.save(save_p); messagebox.showinfo("Success", "Master Template Created!")

if __name__ == "__main__":
    root = tk.Tk(); app = TemplateBuilder(root); root.mainloop()
