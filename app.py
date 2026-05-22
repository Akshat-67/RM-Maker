import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import threading
from extractor import DataExtractor
from processor import TemplateProcessor

class LawApp:
    def __init__(self, root):
        self.root = root
        self.root.title("LegalDoc Automator (v2)")
        self.root.geometry("1100x850")
        self.files = []; self.template_path = ""; self.extracted_data = {}
        self.setup_ui()

    def setup_ui(self):
        f = tk.LabelFrame(self.root, text="1. Select Documents & Template", padx=10, pady=10); f.pack(fill="x", padx=10, pady=5)
        tk.Button(f, text="Add Files (Img/PDF/Txt)", command=self.add_files, width=25).grid(row=0, column=0)
        self.file_list = tk.Listbox(f, height=4, width=80); self.file_list.grid(row=0, column=1, padx=10)
        tk.Button(f, text="Select Master Template", command=self.select_template, width=25).grid(row=1, column=0, pady=5)
        self.template_label = tk.Label(f, text="None selected", fg="blue"); self.template_label.grid(row=1, column=1, sticky="w")

        api_f = tk.Frame(f); api_f.grid(row=2, column=0, columnspan=2, sticky="w")
        tk.Label(api_f, text="Gemini API Key:").pack(side="left")
        self.api_key_entry = tk.Entry(api_f, width=50, show="*"); self.api_key_entry.pack(side="left")

        self.extract_btn = tk.Button(self.root, text="Extract Data (AI)", command=self.start_extraction,
                                     bg="#4CAF50", fg="white", font=("Arial", 11, "bold")); self.extract_btn.pack(pady=5)

        v_f = tk.LabelFrame(self.root, text="2. Verify & Edit Data", padx=10, pady=10); v_f.pack(fill="both", expand=True, padx=10, pady=5)
        self.canvas = tk.Canvas(v_f); self.sb = ttk.Scrollbar(v_f, orient="vertical", command=self.canvas.yview)
        self.scroll_f = tk.Frame(self.canvas); self.canvas.create_window((0,0), window=self.scroll_f, anchor="nw")
        self.canvas.configure(yscrollcommand=self.sb.set)
        self.scroll_f.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.pack(side="left", fill="both", expand=True); self.sb.pack(side="right", fill="y")

    def add_files(self):
        for p in filedialog.askopenfilenames():
            if p not in self.files: self.files.append(p); self.file_list.insert(tk.END, os.path.basename(p))

    def select_template(self):
        p = filedialog.askopenfilename(filetypes=[("Word", "*.docx")]);
        if p: self.template_path = p; self.template_label.config(text=os.path.basename(p))

    def start_extraction(self):
        k = self.api_key_entry.get()
        if not k: messagebox.showerror("Error", "Need API Key"); return
        self.extract_btn.config(state="disabled")
        threading.Thread(target=self.run_extraction, args=(k,)).start()

    def run_extraction(self, k):
        try:
            self.extracted_data = DataExtractor(k).extract_with_ai(self.files)
            self.root.after(0, self.display_data)
        except Exception as e: self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
        finally: self.root.after(0, lambda: self.extract_btn.config(state="normal"))

    def display_data(self):
        for w in self.scroll_f.winfo_children(): w.destroy()
        if "error" in self.extracted_data:
            messagebox.showerror("AI Error", self.extracted_data["error"]); return

        self.ents = {}
        d = self.extracted_data

        # Preamble
        p_f = tk.Frame(self.scroll_f); p_f.pack(fill="x", pady=5)
        self.ents['rd'] = self.create_f(p_f, "RM Execution Date", d.get('rd',''))
        self.ents['ad'] = self.create_f(p_f, "Loan Agreement Date", d.get('ad',''))

        # Borrowers
        tk.Label(self.scroll_f, text="BORROWERS", fg="blue", font=("Arial", 10, "bold")).pack(anchor="w")
        self.ents['bs'] = []
        for i, b in enumerate(d.get('bs', [])):
            lf = tk.LabelFrame(self.scroll_f, text=f"Borrower {i+1}"); lf.pack(fill="x", pady=2)
            row = {k: self.create_f(lf, k, b.get(k,'')) for k in ['s','n','a','r','rn','adr']}
            self.ents['bs'].append(row)

        # Loans
        tk.Label(self.scroll_f, text="LOANS/LANs", fg="blue", font=("Arial", 10, "bold")).pack(anchor="w")
        self.ents['ls'] = []
        for i, l in enumerate(d.get('ls', [])):
            lf = tk.Frame(self.scroll_f); lf.pack(fill="x")
            row = {k: self.create_f(lf, k, l.get(k,'')) for k in ['n','a','w']}
            self.ents['ls'].append(row)

        # Properties
        tk.Label(self.scroll_f, text="PROPERTIES", fg="blue", font=("Arial", 10, "bold")).pack(anchor="w")
        self.ents['ps'] = []
        for i, p in enumerate(d.get('ps', [])):
            lf = tk.LabelFrame(self.scroll_f, text=f"Property {i+1}"); lf.pack(fill="x", pady=2)
            row = {k: self.create_f(lf, k, p.get(k,'')) for k in ['adr','n','s','e','w']}
            self.ents['ps'].append(row)

        # Bank
        tk.Label(self.scroll_f, text="BANK SIGNATORY", fg="blue", font=("Arial", 10, "bold")).pack(anchor="w")
        bs = d.get('bsign', {})
        self.ents['bsign'] = {k: self.create_f(self.scroll_f, k, bs.get(k,'')) for k in ['n','r','rn']}

        # Witnesses
        tk.Label(self.scroll_f, text="WITNESSES", fg="blue", font=("Arial", 10, "bold")).pack(anchor="w")
        self.ents['ws'] = []
        for i, w in enumerate(d.get('ws', [])):
            lf = tk.LabelFrame(self.scroll_f, text=f"Witness {i+1}"); lf.pack(fill="x", pady=2)
            row = {k: self.create_f(lf, k, w.get(k,'')) for k in ['n','r','rn', 'adr']}
            self.ents['ws'].append(row)

        # Docs
        tk.Label(self.scroll_f, text="DOCUMENTS (SCHEDULE II)", fg="blue", font=("Arial", 10, "bold")).pack(anchor="w")
        t = tk.Text(self.scroll_f, height=10); t.pack(fill="x")
        t.insert("1.0", "\n".join([x.get('t','') for x in d.get('ds', [])]))
        self.ents['ds'] = t

        tk.Button(self.scroll_f, text="Generate Word RM", command=self.generate,
                  bg="blue", fg="white", font=("Arial", 12, "bold")).pack(pady=20, fill="x")

    def create_f(self, p, l, v):
        f = tk.Frame(p); f.pack(fill="x", pady=1)
        tk.Label(f, text=l, width=15, anchor="w").pack(side="left")
        e = tk.Entry(f); e.insert(0, str(v)); e.pack(side="left", fill="x", expand=True)
        return e

    def validate_template(self, path):
        """Checks if a template contains potential untagged data."""
        try:
            from docx import Document
            import re
            doc = Document(path)
            text = "\n".join([p.text for p in doc.paragraphs])
            # Regex for potential dates or names that aren't tags
            leaked = re.findall(r'\b(?:19|20)\d{2}\b|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b', text)
            # Remove anything that's inside curly braces
            clean_text = re.sub(r'\{\{.*?\}\}', '', text)
            if leaked:
                # This is a very simple validator to warn the user
                pass
        except: pass

    def generate(self):
        c = {
            'rd': self.ents['rd'].get(),
            'ad': self.ents['ad'].get(),
            'bs': [{k: v.get() for k, v in b.items()} for b in self.ents['bs']],
            'ls': [{k: v.get() for k, v in l.items()} for l in self.ents['ls']],
            'ps': [{k: v.get() for k, v in p.items()} for p in self.ents['ps']],
            'bsign': {k: v.get() for k, v in self.ents['bsign'].items()},
            'ws': [{k: v.get() for k, v in w.items()} for w in self.ents['ws']],
            'ds': [{'t': x.strip()} for x in self.ents['ds'].get("1.0", tk.END).split('\n') if x.strip()]
        }
        sp = filedialog.asksaveasfilename(defaultextension=".docx")
        if sp:
            try:
                TemplateProcessor(self.template_path).generate(c, sp)
                messagebox.showinfo("Done", f"RM Document saved to:\n{sp}")
            except Exception as e: messagebox.showerror("Error", str(e))

if __name__ == "__main__": root = tk.Tk(); LawApp(root); root.mainloop()
