import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import threading
import re
import zipfile
from extractor import DataExtractor
from processor import TemplateProcessor

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
except ImportError:
    DND_FILES = None
    TkinterDnD = None

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
DEFAULT_GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or "AIzaSyDs32YIJx35FDhb9qOa3vTcWDtU-RpL5_w"

class LawApp:
    def __init__(self, root):
        self.root = root
        self.root.title("LegalDoc Automator Pro - RM Generator v4")
        self.root.geometry("1400x980")
        self.root.configure(bg=BG_MAIN)
        self.files = []
        self.extracted_data = {}
        self.template_map = {}
        self.custom_template_path = tk.StringVar(value="")
        self.discover_templates()
        self.setup_ui()

    def discover_templates(self):
        """Automatically scan the templates/ directory to build the template map."""
        self.template_map = {}
        if not os.path.exists("templates"):
            return

        files = []
        for root_dir, _, names in os.walk("templates"):
            parent = os.path.basename(root_dir)
            if parent and parent.lower() != "templates":
                self.template_map.setdefault(parent.upper(), {"Single": {}, "Multiple": {}})
            for name in names:
                if name.lower().endswith(".docx"):
                    files.append(os.path.join(root_dir, name))

        for path in files:
            if not self.docx_has_placeholders(path):
                continue
            # Expected format: BANK_BORR_LOAN.docx (e.g., ICICI_SINGLE_1.docx)
            # Or use a more flexible heuristic if needed
            f = os.path.basename(path)
            parent = os.path.basename(os.path.dirname(path))
            name = os.path.splitext(f)[0]
            parts = name.split("_")
            if len(parts) >= 3 or parent.upper() not in {"", "TEMPLATES"}:
                bank = parent.upper() if parent.upper() not in {"", "TEMPLATES"} else parts[0].upper()
                borr = "Single" if "SINGLE" in f.upper() else "Multiple"
                # Extract loan count
                loan_match = re.search(r'(\d+)', f)
                loan_key = f"{loan_match.group(1)} Loan" if loan_match else "1 Loan"
                if loan_match and int(loan_match.group(1)) >= 3:
                    loan_key = "3+ Loans"
                elif loan_match and int(loan_match.group(1)) == 2:
                    loan_key = "2 Loans"

                if bank not in self.template_map: self.template_map[bank] = {"Single": {}, "Multiple": {}}
                self.template_map[bank][borr][loan_key] = path

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

    def docx_has_placeholders(self, path):
        try:
            with zipfile.ZipFile(path) as zf:
                for name in zf.namelist():
                    if name.startswith("word/") and name.endswith(".xml"):
                        if "{{" in zf.read(name).decode("utf-8", errors="ignore"):
                            return True
        except Exception:
            return False
        return False

    def setup_ui(self):
        header = tk.Frame(self.root, bg=ACCENT_BLUE, height=70)
        header.pack(fill="x")
        tk.Label(header, text="RM GENERATION MODE", fg="white", bg=ACCENT_BLUE, font=("Segoe UI", 16, "bold"), padx=25, pady=20).pack(side="left")
        tk.Label(header, text="Use template_builder.py for new banks", fg="#E8F0FE", bg=ACCENT_BLUE, font=("Segoe UI", 10, "italic")).pack(side="right", padx=25)

        main_c = tk.Frame(self.root, bg=BG_MAIN)
        main_c.pack(fill="both", expand=True, padx=25, pady=25)

        # --- LEFT PANEL (Scrollable) ---
        left_container = tk.Frame(main_c, bg=PANEL_LEFT, width=480, highlightbackground=BORDER_COLOR, highlightthickness=1)
        left_container.pack(side="left", fill="y")
        left_container.pack_propagate(False)

        left_canvas = tk.Canvas(left_container, bg=PANEL_LEFT, highlightthickness=0)
        left_sb = ttk.Scrollbar(left_container, orient="vertical", command=left_canvas.yview)
        left_p = tk.Frame(left_canvas, bg=PANEL_LEFT, padx=20, pady=20)

        left_canvas.create_window((0,0), window=left_p, anchor="nw", width=460)
        left_canvas.configure(yscrollcommand=left_sb.set)

        left_canvas.pack(side="left", fill="both", expand=True)
        left_sb.pack(side="right", fill="y")
        left_p.bind("<Configure>", lambda e: left_canvas.configure(scrollregion=left_canvas.bbox("all")))

        # 1. Case Settings
        sec1 = tk.LabelFrame(left_p, text=" 1. CASE SETTINGS ", font=FONT_HEADER, bg=PANEL_LEFT, fg=ACCENT_BLUE, padx=15, pady=15)
        sec1.pack(fill="x", pady=(0,15))

        tk.Label(left_p, text="Select Bank:", font=FONT_LABEL, bg=PANEL_LEFT).pack(anchor="w")
        banks = list(self.template_map.keys()) if self.template_map else ["ICICI"]
        self.bank_var = tk.StringVar(value=banks[0])
        self.bank_dropdown = ttk.Combobox(left_p, textvariable=self.bank_var, values=banks, font=FONT_LABEL)
        self.bank_dropdown.pack(fill="x", pady=(5, 15))

        tk.Label(sec1, text="Borrower Count:", font=FONT_LABEL, bg=PANEL_LEFT).pack(anchor="w")
        self.borr_var = tk.StringVar(value="Single")
        tk.Radiobutton(sec1, text="Single Borrower", variable=self.borr_var, value="Single", bg=PANEL_LEFT, font=FONT_LABEL).pack(anchor="w")
        tk.Radiobutton(sec1, text="Multiple Borrowers", variable=self.borr_var, value="Multiple", bg=PANEL_LEFT, font=FONT_LABEL).pack(anchor="w", pady=(0, 10))

        tk.Label(sec1, text="Loan Account Count:", font=FONT_LABEL, bg=PANEL_LEFT).pack(anchor="w")
        self.loan_var = tk.StringVar(value="1 Loan")
        tk.Radiobutton(sec1, text="1 Loan Account", variable=self.loan_var, value="1 Loan", bg=PANEL_LEFT, font=FONT_LABEL).pack(anchor="w")
        tk.Radiobutton(sec1, text="2 Loan Accounts", variable=self.loan_var, value="2 Loans", bg=PANEL_LEFT, font=FONT_LABEL).pack(anchor="w")
        tk.Radiobutton(sec1, text="3+ Loan Accounts", variable=self.loan_var, value="3+ Loans", bg=PANEL_LEFT, font=FONT_LABEL).pack(anchor="w")

        # 2. Template Upload
        sec_template = tk.LabelFrame(left_p, text=" 2. RM TEMPLATE ", font=FONT_HEADER, bg=PANEL_LEFT, fg=ACCENT_BLUE, padx=15, pady=15)
        sec_template.pack(fill="x", pady=15)
        tk.Button(sec_template, text="+ USE CUSTOM TEMPLATE DOCX", command=self.choose_template, bg="#E8F0FE", fg=ACCENT_BLUE, font=("Segoe UI", 10, "bold"), bd=0, pady=10, cursor="hand2").pack(fill="x", pady=(0, 8))
        self.template_lbl = tk.Label(sec_template, text="Auto-selecting from templates folder", bg=PANEL_LEFT, fg="#5F6368", font=("Segoe UI", 9), wraplength=390, justify="left")
        self.template_lbl.pack(fill="x", anchor="w")
        tk.Button(sec_template, text="Clear Custom Template", command=self.clear_template, bg="#FFFFFF", fg=BTN_DANGER, bd=1, relief="flat", font=("Segoe UI", 9)).pack(fill="x", pady=(8, 0))

        # 3. Document Upload
        sec2 = tk.LabelFrame(left_p, text=" 3. UPLOAD DOCUMENTS ", font=FONT_HEADER, bg=PANEL_LEFT, fg=ACCENT_BLUE, padx=15, pady=15)
        sec2.pack(fill="x", pady=15)
        tk.Button(sec2, text="+ ADD PHOTOS / PDFS", command=self.add_files, bg=ACCENT_BLUE, fg="white", font=("Segoe UI", 10, "bold"), bd=0, pady=12, cursor="hand2").pack(fill="x", pady=10)
        self.file_list = tk.Listbox(sec2, height=6, bg="#F1F3F4", bd=0, font=("Segoe UI", 9), selectbackground=ACCENT_BLUE)
        self.file_list.pack(fill="both", pady=5)
        if DND_FILES:
            self.file_list.drop_target_register(DND_FILES)
            self.file_list.dnd_bind("<<Drop>>", self.drop_files)
            self.file_list.insert(tk.END, "  Drop files here or use the add button")
        tk.Button(sec2, text="Clear List", command=self.clear_files, bg="#FFFFFF", fg=BTN_DANGER, bd=1, relief="flat", font=("Segoe UI", 9)).pack(fill="x")

        # 4. AI Configuration
        sec3 = tk.LabelFrame(left_p, text=" 4. AI CONFIGURATION ", font=FONT_HEADER, bg=PANEL_LEFT, fg=ACCENT_BLUE, padx=15, pady=15)
        sec3.pack(fill="x", pady=15)
        tk.Label(sec3, text="Gemini API Key:", font=("Segoe UI", 9), bg=PANEL_LEFT).pack(anchor="w")
        self.api_key_entry = tk.Entry(sec3, show="*", bg="#F1F3F4", bd=0, font=FONT_MONO, highlightthickness=1, highlightbackground=BORDER_COLOR)
        self.api_key_entry.insert(0, DEFAULT_GEMINI_API_KEY)
        self.api_key_entry.pack(fill="x", ipady=8, pady=5)

        tk.Label(sec3, text="Select AI Model:", font=("Segoe UI", 9), bg=PANEL_LEFT).pack(anchor="w", pady=(8,0))
        self.model_var = tk.StringVar(value="gemini-1.5-flash")
        self.model_dropdown = ttk.Combobox(sec3, textvariable=self.model_var, values=["gemini-1.5-flash"], font=FONT_LABEL)
        self.model_dropdown.pack(fill="x", pady=5)
        tk.Button(sec3, text="Verify Key & Get Models", command=self.refresh_models, bg="#E8F0FE", fg=ACCENT_BLUE, bd=0, font=("Segoe UI", 9, "bold"), cursor="hand2").pack(fill="x", pady=5)

        self.extract_btn = tk.Button(left_p, text="START AI AUTOMATION", command=self.start_process, bg=BTN_SUCCESS, fg="white", font=("Segoe UI", 12, "bold"), bd=0, pady=18, cursor="hand2")
        self.extract_btn.pack(fill="x", pady=(10, 20))

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
        k = self.api_key_entry.get().strip() or DEFAULT_GEMINI_API_KEY
        if not k: messagebox.showwarning("Key Required", "Gemini API key is missing."); return
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

    def add_file_path(self, path):
        if not path or path in self.files or not os.path.isfile(path):
            return
        if not self.files and self.file_list.size() and self.file_list.get(0).strip().startswith("Drop files here"):
            self.file_list.delete(0, tk.END)
        self.files.append(path)
        self.file_list.insert(tk.END, f"  FILE {os.path.basename(path)}")

    def drop_files(self, event):
        for path in self.root.tk.splitlist(event.data):
            self.add_file_path(path)

    def add_files(self):
        for p in filedialog.askopenfilenames():
            self.add_file_path(p)

    def clear_files(self):
        self.files = []; self.file_list.delete(0, tk.END)
        if DND_FILES:
            self.file_list.insert(tk.END, "  Drop files here or use the add button")

    def choose_template(self):
        path = filedialog.askopenfilename(
            title="Select RM template",
            filetypes=[("Word Document", "*.docx")]
        )
        if not path:
            return
        self.custom_template_path.set(path)
        self.template_lbl.config(text=f"Using: {os.path.basename(path)}")

    def clear_template(self):
        self.custom_template_path.set("")
        self.template_lbl.config(text="Auto-selecting from templates folder")

    def start_process(self):
        k, m = self.api_key_entry.get().strip() or DEFAULT_GEMINI_API_KEY, self.model_var.get()
        if not k or not self.files: messagebox.showerror("Incomplete", "Add files and key first."); return
        self.extract_btn.config(state="disabled", text="AI THINKING...")
        borrower_count = self.expected_borrower_count()
        loan_count = self.expected_loan_count()
        bank = self.bank_var.get()
        threading.Thread(target=self.run_automation, args=(k, m, bank, borrower_count, loan_count)).start()

    def expected_borrower_count(self):
        return 1 if self.borr_var.get() == "Single" else None

    def expected_loan_count(self):
        if self.loan_var.get() == "1 Loan":
            return 1
        if self.loan_var.get() == "2 Loans":
            return 2
        return None

    def run_automation(self, k, m, bank, borrower_count, loan_count):
        try:
            self.root.after(0, lambda: self.status_lbl.config(text="AI is processing documents..."))
            self.extracted_data = DataExtractor(k).extract_with_ai(
                self.files,
                m,
                bank_name=bank,
                expected_borrowers=borrower_count,
                expected_loans=loan_count,
                expected_witnesses=2,
            )
            self.root.after(0, self.display_data)
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda msg=error_msg: messagebox.showerror("AI Error", msg))
        finally:
            self.root.after(0, lambda: self.extract_btn.config(state="normal", text="START AI AUTOMATION"))
            self.root.after(0, lambda: self.status_lbl.config(text="Extraction Complete"))

    def display_data(self):
        for w in self.scroll_f.winfo_children(): w.destroy()
        if "error" in self.extracted_data: messagebox.showerror("Error", self.extracted_data["error"]); return
        self.ents = {}
        d = self.enforce_case_counts(self.extracted_data)
        warnings = self.get_extraction_warnings(d)
        if warnings:
            warn_sec = tk.LabelFrame(self.scroll_f, text=" EXTRACTION WARNINGS ", bg="#FFF8E1", font=FONT_HEADER, padx=15, pady=10)
            warn_sec.pack(fill="x", pady=10)
            tk.Label(warn_sec, text="\n".join(warnings), bg="#FFF8E1", fg="#8A6D00", font=FONT_LABEL, justify="left", wraplength=760).pack(anchor="w")

        # --- GENERAL INFO ---
        sec1 = tk.LabelFrame(self.scroll_f, text=" GENERAL INFO ", bg=PANEL_LEFT, font=FONT_HEADER, padx=15, pady=10); sec1.pack(fill="x", pady=10)
        self.ents['rd'] = self.create_input(sec1, "RM Execution Date", d.get('rd',''))
        self.ents['ad'] = self.create_input(sec1, "Loan Agreement Date", d.get('ad',''))

        # --- BORROWERS ---
        self.borr_container = tk.Frame(self.scroll_f, bg=BG_MAIN)
        self.borr_container.pack(fill="x")
        self.ents['bs'] = []
        for i, b in enumerate(d.get('bs', [])): self.add_borrower_ui(b)
        if self.borr_var.get() == "Multiple":
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

    def enforce_case_counts(self, data):
        data = dict(data)
        borrowers = list(data.get("bs", []))
        loans = list(data.get("ls", []))
        witnesses = list(data.get("ws", []))

        if self.expected_borrower_count() == 1:
            data["bs"] = borrowers[:1] if borrowers else [{}]
        else:
            data["bs"] = borrowers

        if self.expected_loan_count() is not None:
            data["ls"] = loans[:self.expected_loan_count()]
            while len(data["ls"]) < self.expected_loan_count():
                data["ls"].append({})
        else:
            data["ls"] = loans

        data["ws"] = witnesses[:2]
        while len(data["ws"]) < 2:
            data["ws"].append({})

        return data

    def get_extraction_warnings(self, data):
        warnings = []
        borrower_names = {b.get("n", "").strip().casefold() for b in data.get("bs", []) if b.get("n")}
        witness_names = {w.get("n", "").strip().casefold() for w in data.get("ws", []) if w.get("n")}
        if borrower_names.intersection(witness_names):
            warnings.append("A name appears as both borrower and witness. Please verify the borrower/witness sections before generating.")
        if not any(b.get("n", "").strip() for b in data.get("bs", [])):
            warnings.append("No borrower was extracted. Add or correct borrower details before generating.")
        if not data.get("ls"):
            warnings.append("No loan account was extracted. Add loan details before generating.")
        elif self.expected_loan_count() and len([l for l in data.get("ls", []) if l.get("n") or l.get("a")]) < self.expected_loan_count():
            warnings.append(f"{self.expected_loan_count()} loan accounts were selected. Fill any blank loan account before generating.")
        if not data.get("ps"):
            warnings.append("No property schedule was extracted. Add property details before generating.")
        if len(data.get("ws", [])) < 2 or not all(w.get("n", "").strip() for w in data.get("ws", [])[:2]):
            warnings.append("Two witnesses are required. Fill any blank witness details before generating.")
        return warnings

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
        if self.borr_var.get() == "Multiple":
            tk.Button(f, text="Remove Borrower", command=lambda r=row, frame=f: self.remove_entity(self.ents['bs'], r, frame), bg="#FFFFFF", fg=BTN_DANGER, bd=1, relief="flat").pack(anchor="e", pady=(8, 0))

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
        tk.Button(f, text="Remove Loan Account", command=lambda r=row, frame=f: self.remove_entity(self.ents['ls'], r, frame), bg="#FFFFFF", fg=BTN_DANGER, bd=1, relief="flat").pack(anchor="e", pady=(8, 0))

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
        tk.Button(f, text="Remove Property", command=lambda r=row, frame=f: self.remove_entity(self.ents['ps'], r, frame), bg="#FFFFFF", fg=BTN_DANGER, bd=1, relief="flat").pack(anchor="e", pady=(8, 0))

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
        tk.Button(f, text="Remove Witness", command=lambda r=row, frame=f: self.remove_entity(self.ents['ws'], r, frame), bg="#FFFFFF", fg=BTN_DANGER, bd=1, relief="flat").pack(anchor="e", pady=(8, 0))

    def remove_entity(self, collection, row, frame):
        if row in collection:
            collection.remove(row)
        frame.destroy()

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
        t_path = self.custom_template_path.get().strip()
        if not t_path:
            try:
                t_path = self.template_map[bank][borr][loan]
            except KeyError:
                messagebox.showerror("Error", f"No template found for {bank} ({borr}, {loan})"); return
        if not os.path.exists(t_path):
            messagebox.showerror("Error", f"Template not found:\n{t_path}"); return

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
            c = self.enforce_context_counts(c)
            base_name = os.path.splitext(os.path.basename(t_path))[0] if self.custom_template_path.get().strip() else bank
            sp = filedialog.asksaveasfilename(defaultextension=".docx", initialfile=f"RM_{base_name}.docx")
            if sp:
                TemplateProcessor(t_path).generate(c, sp)
                messagebox.showinfo("Success", f"RM Generated successfully at:\n{sp}")
        except Exception as e:
            messagebox.showerror("Generation Error", str(e))

    def enforce_context_counts(self, context):
        if self.expected_borrower_count() == 1:
            context["bs"] = context.get("bs", [])[:1]

        if self.expected_loan_count() is not None:
            context["ls"] = context.get("ls", [])[:self.expected_loan_count()]
            while len(context["ls"]) < self.expected_loan_count():
                context["ls"].append({"n": "", "a": "", "w": "", "t": ""})

        context["ws"] = context.get("ws", [])[:2]
        while len(context["ws"]) < 2:
            context["ws"].append({"n": "", "r": "", "rn": "", "adr": ""})

        return context

if __name__ == "__main__":
    root = TkinterDnD.Tk() if TkinterDnD else tk.Tk()
    LawApp(root)
    root.mainloop()
