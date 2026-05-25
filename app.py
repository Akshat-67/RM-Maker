import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import threading
import re
from extractor import DataExtractor
from processor import TemplateProcessor

# --- DESIGN CONSTANTS ---
BG_MAIN = "#F3F4F6"
PANEL_LEFT = "#FFFFFF"
ACCENT_BLUE = "#1A73E8"
BTN_SUCCESS = "#0F9D58"
BTN_DANGER = "#D93025"
BORDER_COLOR = "#DADCE0"
TEXT_COLOR = "#3C4043"

FONT_HEADER = ("Segoe UI", 12, "bold")
FONT_LABEL = ("Segoe UI", 10)
FONT_MONO = ("Consolas", 10)

class LawApp:
    def __init__(self, root):
        self.root = root
        self.root.title("LegalDoc Automator Pro - RM Generator v4")
        self.root.geometry("1400x980")
        self.root.configure(bg=BG_MAIN)
        self.files = []
        self.extracted_data = {}
        self.template_map = {}
        self.discover_templates()
        self.setup_ui()

    def discover_templates(self):
        """Automatically scan the templates/ directory to build the template map."""
        self.template_map = {}
        if not os.path.exists("templates"):
            return

        files = [f for f in os.listdir("templates") if f.endswith(".docx")]
        for f in files:
            # Expected format: BANK_BORR_LOAN.docx (e.g., ICICI_SINGLE_1.docx)
            # Or use a more flexible heuristic if needed
            name = f.replace(".docx", "")
            parts = name.split("_")
            if len(parts) >= 3:
                bank = parts[0]
                borr = "Single" if "SINGLE" in f.upper() else "Multiple"
                # Extract loan count
                loan_match = re.search(r'(\d+)', f)
                loan_key = f"{loan_match.group(1)} Loan" if loan_match else "1 Loan"
                if loan_match and int(loan_match.group(1)) >= 3:
                    loan_key = "3+ Loans"
                elif loan_match and int(loan_match.group(1)) == 2:
                    loan_key = "2 Loans"

                if bank not in self.template_map: self.template_map[bank] = {"Single": {}, "Multiple": {}}
                self.template_map[bank][borr][loan_key] = os.path.join("templates", f)

        # Fallbacks for banks found but missing specific combinations
        for bank in self.template_map:
            for borr in ["Single", "Multiple"]:
                keys = list(self.template_map[bank][borr].keys())
                if not keys: continue
                # If "1 Loan" missing, use first available
                if "1 Loan" not in self.template_map[bank][borr]:
                    self.template_map[bank][borr]["1 Loan"] = self.template_map[bank][borr][keys[0]]
                if "2 Loans" not in self.template_map[bank][borr]:
                    self.template_map[bank][borr]["2 Loans"] = self.template_map[bank][borr][keys[0]]
                if "3+ Loans" not in self.template_map[bank][borr]:
                    self.template_map[bank][borr]["3+ Loans"] = self.template_map[bank][borr][keys[0]]

    def setup_ui(self):
        header = tk.Frame(self.root, bg=ACCENT_BLUE, height=70)
        header.pack(fill="x")
        tk.Label(header, text="RM GENERATION MODE", fg="white", bg=ACCENT_BLUE, font=("Segoe UI", 16, "bold"), padx=25, pady=20).pack(side="left")
        tk.Label(header, text="Use template_builder.py for new banks", fg="#E8F0FE", bg=ACCENT_BLUE, font=("Segoe UI", 10, "italic")).pack(side="right", padx=25)

        main_c = tk.Frame(self.root, bg=BG_MAIN)
        main_c.pack(fill="both", expand=True, padx=25, pady=25)

        # --- LEFT PANEL ---
        left_p = tk.Frame(main_c, bg=PANEL_LEFT, width=480, padx=25, pady=25, highlightbackground=BORDER_COLOR, highlightthickness=1)
        left_p.pack(side="left", fill="y")
        left_p.pack_propagate(False)

        # 1. Case Settings
        tk.Label(left_p, text="1. CASE SETTINGS", font=FONT_HEADER, bg=PANEL_LEFT, fg=ACCENT_BLUE).pack(anchor="w", pady=(0,15))

        tk.Label(left_p, text="Select Bank:", font=FONT_LABEL, bg=PANEL_LEFT).pack(anchor="w")
        banks = list(self.template_map.keys()) if self.template_map else ["ICICI"]
        self.bank_var = tk.StringVar(value=banks[0])
        self.bank_dropdown = ttk.Combobox(left_p, textvariable=self.bank_var, values=banks, font=FONT_LABEL)
        self.bank_dropdown.pack(fill="x", pady=(5, 15))

        tk.Label(left_p, text="Borrower Count:", font=FONT_LABEL, bg=PANEL_LEFT).pack(anchor="w")
        self.borr_var = tk.StringVar(value="Single")
        tk.Radiobutton(left_p, text="Single Borrower", variable=self.borr_var, value="Single", bg=PANEL_LEFT, font=FONT_LABEL).pack(anchor="w")
        tk.Radiobutton(left_p, text="Multiple Borrowers", variable=self.borr_var, value="Multiple", bg=PANEL_LEFT, font=FONT_LABEL).pack(anchor="w", pady=(0, 10))

        tk.Label(left_p, text="Loan Account Count:", font=FONT_LABEL, bg=PANEL_LEFT).pack(anchor="w")
        self.loan_var = tk.StringVar(value="1 Loan")
        tk.Radiobutton(left_p, text="1 Loan Account", variable=self.loan_var, value="1 Loan", bg=PANEL_LEFT, font=FONT_LABEL).pack(anchor="w")
        tk.Radiobutton(left_p, text="2 Loan Accounts", variable=self.loan_var, value="2 Loans", bg=PANEL_LEFT, font=FONT_LABEL).pack(anchor="w")
        tk.Radiobutton(left_p, text="3+ Loan Accounts", variable=self.loan_var, value="3+ Loans", bg=PANEL_LEFT, font=FONT_LABEL).pack(anchor="w")

        # 2. Document Upload
        tk.Label(left_p, text="\n2. UPLOAD DOCUMENTS", font=FONT_HEADER, bg=PANEL_LEFT, fg=ACCENT_BLUE).pack(anchor="w", pady=(15,5))
        tk.Button(left_p, text="+ ADD PHOTOS / PDFS", command=self.add_files, bg=ACCENT_BLUE, fg="white", font=("Segoe UI", 10, "bold"), bd=0, pady=12, cursor="hand2").pack(fill="x", pady=10)
        self.file_list = tk.Listbox(left_p, height=8, bg="#F1F3F4", bd=0, font=("Segoe UI", 9), selectbackground=ACCENT_BLUE)
        self.file_list.pack(fill="both", pady=5)
        tk.Button(left_p, text="Clear List", command=self.clear_files, bg="#FFFFFF", fg=BTN_DANGER, bd=1, relief="flat", font=("Segoe UI", 9)).pack(fill="x", pady=(0, 15))

        # 3. AI Configuration
        tk.Label(left_p, text="3. AI CONFIGURATION", font=FONT_HEADER, bg=PANEL_LEFT, fg=ACCENT_BLUE).pack(anchor="w", pady=(10,5))
        tk.Label(left_p, text="Paste API Key:", font=("Segoe UI", 9), bg=PANEL_LEFT).pack(anchor="w")
        self.api_key_entry = tk.Entry(left_p, show="*", bg="#F1F3F4", bd=0, font=FONT_MONO)
        self.api_key_entry.pack(fill="x", ipady=10, pady=5)

        tk.Label(left_p, text="Select AI Model:", font=("Segoe UI", 9), bg=PANEL_LEFT).pack(anchor="w", pady=(8,0))
        self.model_var = tk.StringVar(value="gemini-1.5-flash")
        self.model_dropdown = ttk.Combobox(left_p, textvariable=self.model_var, values=["gemini-1.5-flash"], font=FONT_LABEL)
        self.model_dropdown.pack(fill="x", pady=5)
        tk.Button(left_p, text="Verify Key & Get Models", command=self.refresh_models, bg="#E8F0FE", fg=ACCENT_BLUE, bd=0, font=("Segoe UI", 9, "bold"), cursor="hand2").pack(fill="x", pady=5)

        self.extract_btn = tk.Button(left_p, text="START AI AUTOMATION", command=self.start_process, bg=BTN_SUCCESS, fg="white", font=("Segoe UI", 12, "bold"), bd=0, pady=15, cursor="hand2")
        self.extract_btn.pack(fill="x", pady=(20, 0))

        # --- RIGHT PANEL ---
        right_p = tk.Frame(main_c, bg=BG_MAIN, padx=25)
        right_p.pack(side="right", fill="both", expand=True)

        top_bar = tk.Frame(right_p, bg=BG_MAIN)
        top_bar.pack(fill="x", pady=(0, 15))
        tk.Label(top_bar, text="VERIFICATION & EDITING", font=FONT_HEADER, bg=BG_MAIN, fg=TEXT_COLOR).pack(side="left")
        self.status_lbl = tk.Label(top_bar, text="Ready", font=("Segoe UI", 9, "italic"), bg=BG_MAIN, fg="#5F6368")
        self.status_lbl.pack(side="right")

        self.canvas = tk.Canvas(right_p, bg=BG_MAIN, highlightthickness=0)
        self.sb = ttk.Scrollbar(right_p, orient="vertical", command=self.canvas.yview)
        self.scroll_f = tk.Frame(self.canvas, bg=BG_MAIN)
        self.canvas_window = self.canvas.create_window((0,0), window=self.scroll_f, anchor="nw")

        self.canvas.configure(yscrollcommand=self.sb.set)
        self.scroll_f.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.root.bind("<Configure>", lambda e: self.canvas.itemconfig(self.canvas_window, width=self.canvas.winfo_width()))
        self.canvas.pack(side="left", fill="both", expand=True); self.sb.pack(side="right", fill="y")

    def refresh_models(self):
        k = self.api_key_entry.get()
        if not k: messagebox.showwarning("Key Required", "Please paste your Gemini API Key first."); return
        try:
            extractor = DataExtractor(k)
            models = extractor.get_available_models()
            if models:
                self.model_dropdown['values'] = models
                self.model_var.set(models[0])
                messagebox.showinfo("Success", f"Connected! Found {len(models)} models.")
            else: messagebox.showerror("No Models", "Check if API key is valid.")
        except Exception as e: messagebox.showerror("Error", str(e))

    def add_files(self):
        for p in filedialog.askopenfilenames():
            if p not in self.files: self.files.append(p); self.file_list.insert(tk.END, f"  📄 {os.path.basename(p)}")

    def clear_files(self):
        self.files = []; self.file_list.delete(0, tk.END)

    def start_process(self):
        k, m = self.api_key_entry.get(), self.model_var.get()
        if not k or not self.files: messagebox.showerror("Incomplete", "Add files and key first."); return
        self.extract_btn.config(state="disabled", text="AI THINKING...")
        threading.Thread(target=self.run_automation, args=(k,m)).start()

    def run_automation(self, k, m):
        try:
            self.root.after(0, lambda: self.status_lbl.config(text="AI is processing documents..."))
            self.extracted_data = DataExtractor(k).extract_with_ai(self.files, m)
            self.root.after(0, self.display_data)
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("AI Error", str(e)))
        finally:
            self.root.after(0, lambda: self.extract_btn.config(state="normal", text="START AI AUTOMATION"))
            self.root.after(0, lambda: self.status_lbl.config(text="Extraction Complete"))

    def display_data(self):
        for w in self.scroll_f.winfo_children(): w.destroy()
        if "error" in self.extracted_data: messagebox.showerror("Error", self.extracted_data["error"]); return
        self.ents = {}
        d = self.extracted_data

        # --- GENERAL INFO ---
        sec1 = tk.LabelFrame(self.scroll_f, text=" GENERAL INFO ", bg=PANEL_LEFT, font=FONT_HEADER, padx=15, pady=10); sec1.pack(fill="x", pady=10)
        self.ents['rd'] = self.create_input(sec1, "RM Execution Date", d.get('rd',''))
        self.ents['ad'] = self.create_input(sec1, "Loan Agreement Date", d.get('ad',''))

        # --- BORROWERS ---
        self.borr_container = tk.Frame(self.scroll_f, bg=BG_MAIN)
        self.borr_container.pack(fill="x")
        self.ents['bs'] = []
        for i, b in enumerate(d.get('bs', [])): self.add_borrower_ui(b)
        tk.Button(self.scroll_f, text="+ Add Borrower", command=lambda: self.add_borrower_ui({}), bg="#E8F0FE", fg=ACCENT_BLUE).pack(pady=5)

        # --- LOANS ---
        self.loan_container = tk.Frame(self.scroll_f, bg=BG_MAIN)
        self.loan_container.pack(fill="x")
        self.ents['ls'] = []
        for i, l in enumerate(d.get('ls', [])): self.add_loan_ui(l)
        tk.Button(self.scroll_f, text="+ Add Loan Account", command=lambda: self.add_loan_ui({}), bg="#E8F0FE", fg=ACCENT_BLUE).pack(pady=5)

        # --- PROPERTIES ---
        self.prop_container = tk.Frame(self.scroll_f, bg=BG_MAIN)
        self.prop_container.pack(fill="x")
        self.ents['ps'] = []
        for i, p in enumerate(d.get('ps', [])): self.add_property_ui(p)
        tk.Button(self.scroll_f, text="+ Add Property", command=lambda: self.add_property_ui({}), bg="#E8F0FE", fg=ACCENT_BLUE).pack(pady=5)

        # --- WITNESSES ---
        self.wit_container = tk.Frame(self.scroll_f, bg=BG_MAIN)
        self.wit_container.pack(fill="x")
        self.ents['ws'] = []
        for i, w in enumerate(d.get('ws', [])): self.add_witness_ui(w)
        tk.Button(self.scroll_f, text="+ Add Witness", command=lambda: self.add_witness_ui({}), bg="#E8F0FE", fg=ACCENT_BLUE).pack(pady=5)

        # --- LEGAL & SIGNATORY ---
        sec_end = tk.LabelFrame(self.scroll_f, text=" LEGAL & BANK SIGNATORY ", bg=PANEL_LEFT, font=FONT_HEADER, padx=15, pady=10); sec_end.pack(fill="x", pady=10)
        bs = d.get('bsign', {})
        self.ents['bsign'] = {
            'n': self.create_input(sec_end, "Signatory Name", bs.get('n','')),
            'r': self.create_input(sec_end, "Relation", bs.get('r','')),
            'rn': self.create_input(sec_end, "Rel Name", bs.get('rn',''))
        }

        tk.Label(sec_end, text="Document Schedule (ds):", font=FONT_LABEL, bg=PANEL_LEFT, fg="#5F6368").pack(anchor="w", pady=(10, 0))
        t = tk.Text(sec_end, height=8, bg="#F8F9FA", font=FONT_MONO, bd=1, highlightthickness=1, highlightbackground=BORDER_COLOR)
        t.pack(fill="x", pady=5)
        t.insert("1.0", "\n".join([x.get('t','') for x in d.get('ds', [])])); self.ents['ds'] = t

        tk.Button(self.scroll_f, text="VERIFIED: GENERATE FINAL RM DOCX", command=self.generate, bg=ACCENT_BLUE, fg="white", font=("Segoe UI", 13, "bold"), pady=20, bd=0, cursor="hand2").pack(fill="x", pady=40)

    def add_borrower_ui(self, b):
        idx = len(self.ents['bs']) + 1
        f = tk.LabelFrame(self.borr_container, text=f" BORROWER {idx} ", bg=PANEL_LEFT, font=FONT_HEADER, padx=15, pady=10)
        f.pack(fill="x", pady=10)
        row = {
            's': self.create_input(f, "Salutation", b.get('s','')),
            'n': self.create_input(f, "Full Name", b.get('n','')),
            'a': self.create_input(f, "Age", b.get('a','')),
            'r': self.create_input(f, "Relation (S/o)", b.get('r','')),
            'rn': self.create_input(f, "Relative Name", b.get('rn','')),
            'adr': self.create_input(f, "Address", b.get('adr',''), True),
            'id': self.create_input(f, "Aadhar/ID", b.get('id',''))
        }
        self.ents['bs'].append(row)

    def add_loan_ui(self, l):
        idx = len(self.ents['ls']) + 1
        f = tk.LabelFrame(self.loan_container, text=f" LOAN ACCOUNT {idx} ", bg=PANEL_LEFT, font=FONT_HEADER, padx=15, pady=10)
        f.pack(fill="x", pady=10)
        row = {
            'n': self.create_input(f, "LAN No", l.get('n','')),
            'a': self.create_input(f, "Amount (Figures)", l.get('a','')),
            'w': self.create_input(f, "Amount (Words)", l.get('w',''), True),
            't': self.create_input(f, "Tenure", l.get('t',''))
        }
        self.ents['ls'].append(row)

    def add_property_ui(self, p):
        idx = len(self.ents['ps']) + 1
        f = tk.LabelFrame(self.prop_container, text=f" PROPERTY {idx} ", bg=PANEL_LEFT, font=FONT_HEADER, padx=15, pady=10)
        f.pack(fill="x", pady=10)
        row = {
            'adr': self.create_input(f, "Full Address", p.get('adr',''), True),
            'n': self.create_input(f, "North", p.get('n','')),
            's': self.create_input(f, "South", p.get('s','')),
            'e': self.create_input(f, "East", p.get('e','')),
            'w': self.create_input(f, "West", p.get('w',''))
        }
        self.ents['ps'].append(row)

    def add_witness_ui(self, w):
        idx = len(self.ents['ws']) + 1
        f = tk.LabelFrame(self.wit_container, text=f" WITNESS {idx} ", bg=PANEL_LEFT, font=FONT_HEADER, padx=15, pady=10)
        f.pack(fill="x", pady=10)
        row = {
            'n': self.create_input(f, "Full Name", w.get('n','')),
            'r': self.create_input(f, "Relation", w.get('r','')),
            'rn': self.create_input(f, "Rel Name", w.get('rn','')),
            'adr': self.create_input(f, "Address", w.get('adr',''), True)
        }
        self.ents['ws'].append(row)

    def create_input(self, parent, label, value, is_long=False):
        f = tk.Frame(parent, bg=PANEL_LEFT)
        f.pack(fill="x", pady=6)
        tk.Label(f, text=label, width=20, anchor="w", bg=PANEL_LEFT, font=FONT_LABEL, fg="#5F6368").pack(side="left")

        if is_long:
            e = tk.Text(f, bg="#F1F3F4", font=FONT_LABEL, height=3, bd=0, highlightthickness=1, highlightbackground=BORDER_COLOR)
            e.insert("1.0", str(value))
            e.pack(side="left", fill="x", expand=True, pady=2)
            e.bind("<FocusIn>", lambda event: e.config(highlightbackground=ACCENT_BLUE))
            e.bind("<FocusOut>", lambda event: e.config(highlightbackground=BORDER_COLOR))
        else:
            e = tk.Entry(f, bg="#F1F3F4", bd=0, font=FONT_LABEL, highlightthickness=1, highlightbackground=BORDER_COLOR)
            e.insert(0, str(value))
            e.pack(side="left", fill="x", expand=True, ipady=8)
            e.bind("<FocusIn>", lambda event: e.config(highlightbackground=ACCENT_BLUE))
            e.bind("<FocusOut>", lambda event: e.config(highlightbackground=BORDER_COLOR))

        return e

    def get_val(self, e):
        if isinstance(e, tk.Text): return e.get("1.0", tk.END).strip()
        return e.get()

    def generate(self):
        bank, borr, loan = self.bank_var.get(), self.borr_var.get(), self.loan_var.get()
        try:
            t_path = self.template_map[bank][borr][loan]
        except KeyError:
            messagebox.showerror("Error", f"No template found for {bank} ({borr}, {loan})"); return

        try:
            c = {
                'rd': self.get_val(self.ents['rd']),
                'ad': self.get_val(self.ents['ad']),
                'bs': [{k: self.get_val(v) for k, v in b.items()} for b in self.ents['bs']],
                'ls': [{k: self.get_val(v) for k, v in l.items()} for l in self.ents['ls']],
                'ps': [{k: self.get_val(v) for k, v in p.items()} for p in self.ents['ps']],
                'ws': [{k: self.get_val(v) for k, v in w.items()} for w in self.ents['ws']],
                'bsign': {k: self.get_val(v) for k, v in self.ents['bsign'].items()},
                'ds': [{'t': x.strip()} for x in self.get_val(self.ents['ds']).split('\n') if x.strip()]
            }
            sp = filedialog.asksaveasfilename(defaultextension=".docx", initialfile=f"RM_{bank}.docx")
            if sp:
                TemplateProcessor(t_path).generate(c, sp)
                messagebox.showinfo("Success", f"RM Generated successfully at:\n{sp}")
        except Exception as e:
            messagebox.showerror("Generation Error", str(e))

if __name__ == "__main__": root = tk.Tk(); LawApp(root); root.mainloop()
