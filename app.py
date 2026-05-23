import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import threading
from extractor import DataExtractor
from processor import TemplateProcessor

class LawApp:
    def __init__(self, root):
        self.root = root
        self.root.title("LegalDoc Automator v3 - Automated RM Generation")
        self.root.geometry("1200x900")

        self.files = []
        self.extracted_data = {}

        # Template Mapping
        self.template_map = {
            "ICICI": {
                "Single": {
                    "1 Loan": "templates/ICICI_SINGLE_BORROWER_1_LOAN.docx",
                    "2 Loans": "templates/ICICI_SINGLE_BORROWER_2_LOANS.docx",
                    "3+ Loans": "templates/ICICI_SINGLE_BORROWER_3_LOANS.docx"
                },
                "Multiple": {
                    "1 Loan": "templates/ICICI_MULTI_BORROWER_2_LOANS.docx", # Default for now
                    "2 Loans": "templates/ICICI_MULTI_BORROWER_2_LOANS.docx",
                    "3+ Loans": "templates/ICICI_MULTI_BORROWER_2_LOANS.docx"
                }
            }
        }

        self.setup_ui()

    def setup_ui(self):
        # --- LEFT PANEL: Settings & File Dump ---
        left_panel = tk.Frame(self.root, width=400, bg="#f0f0f0", padx=10, pady=10)
        left_panel.pack(side="left", fill="y")

        tk.Label(left_panel, text="1. SETTINGS", font=("Arial", 12, "bold"), bg="#f0f0f0").pack(anchor="w")

        # Bank Selection
        tk.Label(left_panel, text="Select Bank:", bg="#f0f0f0").pack(anchor="w", pady=(10, 0))
        self.bank_var = tk.StringVar(value="ICICI")
        ttk.Combobox(left_panel, textvariable=self.bank_var, values=["ICICI", "Home First", "Piramal"]).pack(fill="x")

        # Borrower Count
        tk.Label(left_panel, text="Borrowers:", bg="#f0f0f0").pack(anchor="w", pady=(10, 0))
        self.borr_var = tk.StringVar(value="Single")
        tk.Radiobutton(left_panel, text="Single Borrower", variable=self.borr_var, value="Single", bg="#f0f0f0").pack(anchor="w")
        tk.Radiobutton(left_panel, text="Multiple Borrowers", variable=self.borr_var, value="Multiple", bg="#f0f0f0").pack(anchor="w")

        # Loan Count
        tk.Label(left_panel, text="Sanctions/Loans:", bg="#f0f0f0").pack(anchor="w", pady=(10, 0))
        self.loan_var = tk.StringVar(value="1 Loan")
        tk.Radiobutton(left_panel, text="1 Loan", variable=self.loan_var, value="1 Loan", bg="#f0f0f0").pack(anchor="w")
        tk.Radiobutton(left_panel, text="2 Loans", variable=self.loan_var, value="2 Loans", bg="#f0f0f0").pack(anchor="w")
        tk.Radiobutton(left_panel, text="3+ Loans", variable=self.loan_var, value="3+ Loans", bg="#f0f0f0").pack(anchor="w")

        # File Dump
        tk.Label(left_panel, text="\n2. DUMP DOCUMENTS", font=("Arial", 12, "bold"), bg="#f0f0f0").pack(anchor="w")
        tk.Button(left_panel, text="Add All Files (Photos/PDFs)", command=self.add_files, bg="#2196F3", fg="white").pack(fill="x", pady=5)
        tk.Button(left_panel, text="Clear List", command=self.clear_files).pack(fill="x")

        self.file_list = tk.Listbox(left_panel, height=15)
        self.file_list.pack(fill="both", expand=True, pady=10)

        # API Key
        tk.Label(left_panel, text="Gemini API Key:", bg="#f0f0f0").pack(anchor="w")
        self.api_key_entry = tk.Entry(left_panel, show="*")
        self.api_key_entry.pack(fill="x")
        tk.Button(left_panel, text="Test Connection", command=self.test_connection, bg="#9E9E9E", fg="white", font=("Arial", 9)).pack(fill="x", pady=2)

        self.extract_btn = tk.Button(left_panel, text="START AUTOMATION", command=self.start_process,
                                     bg="#4CAF50", fg="white", font=("Arial", 11, "bold"), height=2)
        self.extract_btn.pack(fill="x", pady=20)

        # --- RIGHT PANEL: Verification & Edit ---
        right_panel = tk.Frame(self.root, padx=10, pady=10)
        right_panel.pack(side="right", fill="both", expand=True)

        tk.Label(right_panel, text="3. VERIFY & GENERATE", font=("Arial", 12, "bold")).pack(anchor="w")

        self.canvas = tk.Canvas(right_panel)
        self.scrollbar = ttk.Scrollbar(right_panel, orient="vertical", command=self.canvas.yview)
        self.scroll_f = tk.Frame(self.canvas)
        self.scroll_f.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas_window = self.canvas.create_window((0,0), window=self.scroll_f, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.root.bind("<Configure>", lambda e: self.canvas.itemconfig(self.canvas_window, width=self.canvas.winfo_width()))

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

    def add_files(self):
        for p in filedialog.askopenfilenames():
            if p not in self.files: self.files.append(p); self.file_list.insert(tk.END, os.path.basename(p))

    def clear_files(self):
        self.files = []; self.file_list.delete(0, tk.END)

    def test_connection(self):
        k = self.api_key_entry.get()
        if not k: messagebox.showwarning("Warning", "Please enter an API Key first."); return
        try:
            import google.generativeai as genai
            genai.configure(api_key=k)
            models = [m.name for m in genai.list_models()]
            messagebox.showinfo("Success", f"Connection successful!\nFound models: {len(models)}")
        except Exception as e:
            messagebox.showerror("Connection Failed", f"Could not connect to Google AI:\n{str(e)}\n\nSuggestions:\n1. Check your internet.\n2. Ensure 'Generative Language API' is enabled in Google Cloud Console.")

    def start_process(self):
        k = self.api_key_entry.get()
        if not k or not self.files: messagebox.showerror("Error", "Dump files and enter API Key first."); return

        self.extract_btn.config(state="disabled", text="AI Processing...")
        threading.Thread(target=self.run_automation, args=(k,)).start()

    def run_automation(self, k):
        try:
            self.extracted_data = DataExtractor(k).extract_with_ai(self.files)
            self.root.after(0, self.display_data)
        except Exception as e: self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
        finally: self.root.after(0, lambda: self.extract_btn.config(state="normal", text="START AUTOMATION"))

    def display_data(self):
        for w in self.scroll_f.winfo_children(): w.destroy()
        if "error" in self.extracted_data:
            messagebox.showerror("AI Error", self.extracted_data["error"]); return

        self.ents = {}
        d = self.extracted_data

        # UI Logic for dynamic fields
        self.ents['rd'] = self.create_f(self.scroll_f, "RM Execution Date", d.get('rd',''))
        self.ents['ad'] = self.create_f(self.scroll_f, "Loan Agreement Date", d.get('ad',''))

        # Borrowers
        self.ents['bs'] = []
        for i, b in enumerate(d.get('bs', [])):
            lf = tk.LabelFrame(self.scroll_f, text=f"Borrower {i+1}"); lf.pack(fill="x", pady=2)
            row = {k: self.create_f(lf, k, b.get(k,'')) for k in ['s','n','a','r','rn','adr']}
            self.ents['bs'].append(row)

        # Loans
        self.ents['ls'] = []
        for i, l in enumerate(d.get('ls', [])):
            lf = tk.Frame(self.scroll_f); lf.pack(fill="x")
            row = {k: self.create_f(lf, k, l.get(k,'')) for k in ['n','a','w','t']}
            self.ents['ls'].append(row)

        # Properties
        self.ents['ps'] = []
        for i, p in enumerate(d.get('ps', [])):
            lf = tk.LabelFrame(self.scroll_f, text=f"Property {i+1}"); lf.pack(fill="x", pady=2)
            row = {k: self.create_f(lf, k, p.get(k,'')) for k in ['adr','n','s','e','w']}
            self.ents['ps'].append(row)

        # Bank/Witness/Docs
        tk.Label(self.scroll_f, text="Signatories & Witnesses", fg="blue", font=("Arial", 10, "bold")).pack(anchor="w", pady=10)
        bs = d.get('bsign', {})
        self.ents['bsign'] = {k: self.create_f(self.scroll_f, f"Bank Rep {k}", bs.get(k,'')) for k in ['n','r','rn']}

        self.ents['ws'] = []
        for i, w in enumerate(d.get('ws', [])):
            row = {k: self.create_f(self.scroll_f, f"W{i+1} {k}", w.get(k,'')) for k in ['n','r','rn', 'adr']}
            self.ents['ws'].append(row)

        tk.Label(self.scroll_f, text="Second Schedule (Title Chain)").pack(anchor="w")
        t = tk.Text(self.scroll_f, height=8); t.pack(fill="x")
        t.insert("1.0", "\n".join([x.get('t','') for x in d.get('ds', [])]))
        self.ents['ds'] = t

        tk.Button(self.scroll_f, text="GENERATE FINAL RM DOCX", command=self.generate,
                  bg="blue", fg="white", font=("Arial", 12, "bold"), height=2).pack(pady=20, fill="x")

    def create_f(self, p, l, v):
        f = tk.Frame(p); f.pack(fill="x", pady=1)
        tk.Label(f, text=l, width=20, anchor="w").pack(side="left")
        e = tk.Entry(f); e.insert(0, str(v)); e.pack(side="left", fill="x", expand=True)
        return e

    def generate(self):
        # Auto-select template
        bank = self.bank_var.get()
        borr = self.borr_var.get()
        loan = self.loan_var.get()

        try:
            t_path = self.template_map[bank][borr][loan]
        except KeyError:
            messagebox.showerror("Error", f"No template found for {bank} {borr} {loan}"); return

        context = {
            'rd': self.ents['rd'].get(),
            'ad': self.ents['ad'].get(),
            'bs': [{k: v.get() for k, v in b.items()} for b in self.ents['bs']],
            'ls': [{k: v.get() for k, v in l.items()} for l in self.ents['ls']],
            'ps': [{k: v.get() for k, v in p.items()} for p in self.ents['ps']],
            'bsign': {k: v.get() for k, v in self.ents['bsign'].items()},
            'ws': [{k: v.get() for k, v in w.items()} for w in self.ents['ws']],
            'ds': [{'t': x.strip()} for x in self.ents['ds'].get("1.0", tk.END).split('\n') if x.strip()]
        }

        save_p = filedialog.asksaveasfilename(defaultextension=".docx")
        if save_p:
            TemplateProcessor(t_path).generate(context, save_p)
            messagebox.showinfo("Success", f"RM Document Generated using:\n{t_path}")

if __name__ == "__main__":
    root = tk.Tk(); LawApp(root); root.mainloop()
