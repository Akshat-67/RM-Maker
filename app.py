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

# --- DESIGN CONSTANTS (MODERN PROFESSIONAL ENTERPRISE) ---
BG_MAIN = "#F8FAFC"
SURFACE_CARD = "#FFFFFF"
PRIMARY_NAV = "#0F172A"
ACCENT_BLUE = "#2563EB"
BTN_SUCCESS = "#10B981"
BTN_DANGER = "#EF4444"
BORDER_COLOR = "#E2E8F0"
TEXT_PRIMARY = "#1E293B"
TEXT_SECONDARY = "#64748B"

FONT_DISPLAY = ("Segoe UI", 14, "bold")
FONT_HEADER = ("Segoe UI", 11, "bold")
FONT_LABEL = ("Segoe UI", 10)
FONT_MONO = ("JetBrains Mono", 9) if os.name == "nt" else ("Courier New", 9)
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
        header = tk.Frame(self.root, bg=PRIMARY_NAV, height=70)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)
        tk.Label(header, text="LegalDoc Automator Pro", bg=PRIMARY_NAV, fg="white", font=("Segoe UI", 18, "bold"), padx=30).pack(side="left")
        tk.Label(header, text="RM GENERATION ENGINE v4.1", bg=PRIMARY_NAV, fg="#94A3B8", font=("Segoe UI", 9, "bold"), padx=30).pack(side="right")

        main_body = tk.Frame(self.root, bg=BG_MAIN)
        main_body.pack(fill="both", expand=True)

        self.left_p_container = tk.Frame(main_body, bg=SURFACE_CARD, width=400, bd=0, highlightthickness=1, highlightbackground=BORDER_COLOR)
        self.left_p_container.pack(side="left", fill="y", padx=(20, 10), pady=20)
        self.left_p_container.pack_propagate(False)

        canvas_l = tk.Canvas(self.left_p_container, bg=SURFACE_CARD, highlightthickness=0)
        scroll_l = ttk.Scrollbar(self.left_p_container, orient="vertical", command=canvas_l.yview)
        self.left_p = tk.Frame(canvas_l, bg=SURFACE_CARD, padx=20)
        self.left_p.bind("<Configure>", lambda e: canvas_l.configure(scrollregion=canvas_l.bbox("all")))
        canvas_l.create_window((0, 0), window=self.left_p, anchor="nw", width=360)
        canvas_l.configure(yscrollcommand=scroll_l.set)
        canvas_l.pack(side="left", fill="both", expand=True)
        scroll_l.pack(side="right", fill="y")

        self.right_p_container = tk.Frame(main_body, bg=BG_MAIN)
        self.right_p_container.pack(side="left", fill="both", expand=True, padx=(10, 20), pady=0)

        # 1. CASE SETTINGS
        self.create_section_title(self.left_p, "1. CASE SETTINGS")
        cs_card = self.create_card(self.left_p)
        tk.Label(cs_card, text="Borrower Count:", bg=SURFACE_CARD, font=FONT_HEADER, fg=TEXT_SECONDARY).pack(anchor="w")
        self.borr_var = tk.StringVar(value="Single")
        tk.Radiobutton(cs_card, text="Single Borrower", variable=self.borr_var, value="Single", bg=SURFACE_CARD, font=FONT_LABEL, command=self.on_settings_change).pack(anchor="w", pady=2)
        tk.Radiobutton(cs_card, text="Multiple Borrowers", variable=self.borr_var, value="Multiple", bg=SURFACE_CARD, font=FONT_LABEL, command=self.on_settings_change).pack(anchor="w", pady=(0, 10))

        tk.Label(cs_card, text="Loan Account Count:", bg=SURFACE_CARD, font=FONT_HEADER, fg=TEXT_SECONDARY).pack(anchor="w")
        self.loan_var = tk.StringVar(value="1 Loan")
        tk.Radiobutton(cs_card, text="1 Loan Account", variable=self.loan_var, value="1 Loan", bg=SURFACE_CARD, font=FONT_LABEL, command=self.on_settings_change).pack(anchor="w")
        tk.Radiobutton(cs_card, text="2 Loan Accounts", variable=self.loan_var, value="2 Loans", bg=SURFACE_CARD, font=FONT_LABEL, command=self.on_settings_change).pack(anchor="w")
        tk.Radiobutton(cs_card, text="3+ Loan Accounts", variable=self.loan_var, value="3+ Loans", bg=SURFACE_CARD, font=FONT_LABEL, command=self.on_settings_change).pack(anchor="w", pady=(0, 10))

        tk.Label(self.left_p, text="Select Bank:", bg=SURFACE_CARD, font=FONT_HEADER, fg=TEXT_SECONDARY).pack(anchor="w", pady=(10,0))
        banks = sorted(list(self.template_map.keys())) if self.template_map else ["ICICI"]
        self.bank_var = tk.StringVar(value=banks[0])
        self.bank_dropdown = ttk.Combobox(self.left_p, textvariable=self.bank_var, values=banks, font=FONT_LABEL, state="readonly")
        self.bank_dropdown.pack(fill="x", pady=(5, 15))

        # 2. RM TEMPLATE
        self.create_section_title(self.left_p, "2. RM TEMPLATE")
        tm_card = self.create_card(self.left_p)
        tk.Button(tm_card, text="+ USE CUSTOM TEMPLATE DOCX", command=self.choose_template, bg="#EBF2FF", fg=ACCENT_BLUE, font=("Segoe UI", 9, "bold"), bd=0, pady=12, cursor="hand2").pack(fill="x")
        self.template_lbl = tk.Label(tm_card, text="Auto-selecting template", bg=SURFACE_CARD, fg=TEXT_SECONDARY, font=("Segoe UI", 8), wraplength=300)
        self.template_lbl.pack(pady=5)
        tk.Button(tm_card, text="Clear Custom Template", command=self.clear_template, bg=SURFACE_CARD, fg=BTN_DANGER, font=("Segoe UI", 8, "underline"), bd=0, cursor="hand2").pack()

        # 3. UPLOAD DOCUMENTS
        self.create_section_title(self.left_p, "3. UPLOAD DOCUMENTS")
        up_card = self.create_card(self.left_p)
        self.drop_zone = tk.Label(up_card, text="Drag & Drop Files Here", bg="#F8FAFC", fg=TEXT_SECONDARY, font=("Segoe UI", 10, "italic"), bd=1, relief="dash", height=4)
        self.drop_zone.pack(fill="x")
        if TkinterDnD:
            self.drop_zone.drop_target_register(DND_FILES)
            self.drop_zone.dnd_bind("<<Drop>>", self.drop_files)
        tk.Button(up_card, text="Browse Files", command=self.add_files, bg=SURFACE_CARD, fg=ACCENT_BLUE, font=("Segoe UI", 9, "bold"), bd=0, cursor="hand2").pack(pady=5)
        self.file_listbox = tk.Listbox(up_card, height=4, font=FONT_MONO, bd=0, highlightthickness=1, highlightbackground=BORDER_COLOR)
        self.file_listbox.pack(fill="x", pady=5)
        tk.Button(up_card, text="Clear All Files", command=self.clear_files, bg=SURFACE_CARD, fg=BTN_DANGER, font=("Segoe UI", 8), bd=0, cursor="hand2").pack(anchor="e")

        # 4. AI CONFIGURATION
        self.create_section_title(self.left_p, "4. AI CONFIGURATION")
        ai_card = self.create_card(self.left_p)
        tk.Label(ai_card, text="Gemini API Key:", bg=SURFACE_CARD, font=FONT_LABEL).pack(anchor="w")
        self.key_ent = tk.Entry(ai_card, show="*", font=FONT_MONO, bd=0, highlightthickness=1, highlightbackground=BORDER_COLOR)
        self.key_ent.insert(0, DEFAULT_GEMINI_API_KEY)
        self.key_ent.pack(fill="x", ipady=8, pady=5)
        tk.Label(ai_card, text="AI Model:", bg=SURFACE_CARD, font=FONT_LABEL).pack(anchor="w", pady=(10,0))
        self.model_var = tk.StringVar(value="gemini-1.5-flash")
        self.model_dropdown = ttk.Combobox(ai_card, textvariable=self.model_var, values=["gemini-1.5-flash", "gemini-2.0-flash-exp"], font=FONT_LABEL)
        self.model_dropdown.pack(fill="x", pady=5)
        tk.Button(ai_card, text="Verify Key & Get Models", command=self.refresh_models, bg=SURFACE_CARD, fg=ACCENT_BLUE, font=("Segoe UI", 8), bd=0, cursor="hand2").pack()

        self.btn_extract = tk.Button(self.left_p, text="START AI AUTOMATION", command=self.start_process, bg=ACCENT_BLUE, fg="white", font=("Segoe UI", 12, "bold"), pady=15, bd=0, cursor="hand2")
        self.btn_extract.pack(fill="x", pady=30)
        self.status_var = tk.StringVar(value="Ready")
        tk.Label(self.left_p, textvariable=self.status_var, bg=SURFACE_CARD, fg=TEXT_SECONDARY, font=("Segoe UI", 9, "italic")).pack()

        # RIGHT PANEL (Scrollable)
        canvas_r = tk.Canvas(self.right_p_container, bg=BG_MAIN, highlightthickness=0)
        scroll_r = ttk.Scrollbar(self.right_p_container, orient="vertical", command=canvas_r.yview)
        self.scroll_f = tk.Frame(canvas_r, bg=BG_MAIN, padx=20)
        self.scroll_f.bind("<Configure>", lambda e: canvas_r.configure(scrollregion=canvas_r.bbox("all")))
        canvas_r.create_window((0, 0), window=self.scroll_f, anchor="nw", width=900)
        canvas_r.configure(yscrollcommand=scroll_r.set)
        canvas_r.pack(side="left", fill="both", expand=True)
        scroll_r.pack(side="right", fill="y")

        self.ents = {"bs": [], "ls": [], "ps": [], "ws": []}
        self.display_data()

    def create_section_title(self, parent, text):
        f = tk.Frame(parent, bg=parent["bg"])
        f.pack(fill="x", pady=(25, 12))
        tk.Label(f, text=text, bg=parent["bg"], fg=PRIMARY_NAV, font=FONT_DISPLAY, anchor="w").pack(side="left")
        tk.Frame(f, bg=BORDER_COLOR, height=1).pack(side="left", fill="x", expand=True, padx=(15, 0))

    def create_card(self, parent, title=None, is_danger=False):
        card = tk.Frame(parent, bg=SURFACE_CARD, bd=0, highlightthickness=1,
                        highlightbackground=BTN_DANGER if is_danger else BORDER_COLOR)
        card.pack(fill="x", pady=10)
        inner = tk.Frame(card, bg=SURFACE_CARD, padx=18, pady=18)
        inner.pack(fill="both", expand=True)
        if title:
            header_f = tk.Frame(inner, bg=SURFACE_CARD)
            header_f.pack(fill="x", pady=(0, 15))
            tk.Label(header_f, text=title, bg=SURFACE_CARD, fg=TEXT_SECONDARY, font=FONT_HEADER, anchor="w").pack(side="left")
        return inner
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
        if "error" in self.extracted_data:
            messagebox.showerror("Error", self.extracted_data["error"])
            return

        self.ents = {"bs": [], "ls": [], "ps": [], "ws": []}
        d = self.enforce_case_counts(self.extracted_data)

        tk.Label(self.scroll_f, text="VERIFICATION & EDITING", font=("Segoe UI", 18, "bold"), bg=BG_MAIN, fg=PRIMARY_NAV).pack(anchor="w", pady=(10, 5))
        tk.Label(self.scroll_f, text="Review extracted data before generating final document", font=("Segoe UI", 10), bg=BG_MAIN, fg=TEXT_SECONDARY).pack(anchor="w", pady=(0, 20))

        warnings = self.get_extraction_warnings(d)
        if warnings:
            warn_card = self.create_card(self.scroll_f, "EXTRACTION WARNINGS", is_danger=True)
            tk.Label(warn_card, text="\n".join(warnings), bg=SURFACE_CARD, fg=BTN_DANGER, font=FONT_LABEL, justify="left", wraplength=760).pack(anchor="w")

        dates_card = self.create_card(self.scroll_f, "EXECUTION DATES")
        self.ents["rd"] = self.create_input(dates_card, "RM Execution Date", d.get("rd", ""))
        self.ents["ad"] = self.create_input(dates_card, "Loan Agreement Date", d.get("ad", ""))

        self.create_section_title(self.scroll_f, "BORROWERS")
        self.borr_container = tk.Frame(self.scroll_f, bg=BG_MAIN); self.borr_container.pack(fill="x")
        for b in d.get("bs", []): self.add_borrower_ui(b)
        tk.Button(self.scroll_f, text="+ Add Borrower", command=lambda: self.add_borrower_ui({}), bg=BG_MAIN, fg=ACCENT_BLUE, font=("Segoe UI", 9, "bold"), bd=0, cursor="hand2").pack(anchor="w")

        self.create_section_title(self.scroll_f, "LOAN ACCOUNTS")
        self.loan_container = tk.Frame(self.scroll_f, bg=BG_MAIN); self.loan_container.pack(fill="x")
        for l in d.get("ls", []): self.add_loan_ui(l)
        tk.Button(self.scroll_f, text="+ Add Loan Account", command=lambda: self.add_loan_ui({}), bg=BG_MAIN, fg=ACCENT_BLUE, font=("Segoe UI", 9, "bold"), bd=0, cursor="hand2").pack(anchor="w")

        self.create_section_title(self.scroll_f, "PROPERTY SCHEDULES")
        self.prop_container = tk.Frame(self.scroll_f, bg=BG_MAIN); self.prop_container.pack(fill="x")
        for p in d.get("ps", []): self.add_property_ui(p)
        tk.Button(self.scroll_f, text="+ Add Property", command=lambda: self.add_property_ui({}), bg=BG_MAIN, fg=ACCENT_BLUE, font=("Segoe UI", 9, "bold"), bd=0, cursor="hand2").pack(anchor="w")

        self.create_section_title(self.scroll_f, "BANK SIGNATORY")
        bsign_card = self.create_card(self.scroll_f)
        sig = d.get("bsign", {})
        self.ents["bsign"] = {
            "n": self.create_input(bsign_card, "Name", sig.get("n", "")),
            "r": self.create_input(bsign_card, "Relation", sig.get("r", "")),
            "rn": self.create_input(bsign_card, "Rel Name", sig.get("rn", ""))
        }

        self.create_section_title(self.scroll_f, "WITNESSES")
        self.wit_container = tk.Frame(self.scroll_f, bg=BG_MAIN); self.wit_container.pack(fill="x")
        for w in d.get("ws", []): self.add_witness_ui(w)
        tk.Button(self.scroll_f, text="+ Add Witness", command=lambda: self.add_witness_ui({}), bg=BG_MAIN, fg=ACCENT_BLUE, font=("Segoe UI", 9, "bold"), bd=0, cursor="hand2").pack(anchor="w")

        self.create_section_title(self.scroll_f, "DOCUMENT SCHEDULE (ds)")
        ds_card = self.create_card(self.scroll_f)
        t = tk.Text(ds_card, height=8, bg="#F8FAFC", font=FONT_MONO, bd=0, highlightthickness=1, highlightbackground=BORDER_COLOR)
        t.pack(fill="x")
        t.insert("1.0", "\n".join([x.get("t","") for x in d.get("ds", [])])); self.ents["ds"] = t

        tk.Button(self.scroll_f, text="VERIFIED: GENERATE FINAL RM DOCX", command=self.generate, bg=BTN_SUCCESS, fg="white", font=("Segoe UI", 13, "bold"), pady=20, bd=0, cursor="hand2").pack(fill="x", pady=40)
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
        idx = len(self.ents["bs"]) + 1
        f = self.create_card(self.borr_container, f"BORROWER {idx}")
        row = {
            "s": self.create_input(f, "Salutation", b.get("s","")),
            "n": self.create_input(f, "Full Name", b.get("n","")),
            "a": self.create_input(f, "Age", b.get("a","")),
            "r": self.create_input(f, "Relation", b.get("r","")),
            "rn": self.create_input(f, "Rel Name", b.get("rn","")),
            "adr": self.create_input(f, "Address", b.get("adr",""), True),
            "id": self.create_input(f, "Aadhar/ID", b.get("id",""))
        }
        self.ents["bs"].append(row)
        tk.Button(f, text="Remove Borrower", command=lambda r=row, fr=f.master.master: self.remove_entity(self.ents["bs"], r, fr), bg=SURFACE_CARD, fg=BTN_DANGER, font=("Segoe UI", 8, "bold"), bd=0, cursor="hand2").pack(anchor="e")
    def add_loan_ui(self, l):
        idx = len(self.ents["ls"]) + 1
        f = self.create_card(self.loan_container, f"LOAN ACCOUNT {idx}")
        row = {
            "n": self.create_input(f, "LAN No", l.get("n","")),
            "a": self.create_input(f, "Amount (Figures)", l.get("a","")),
            "w": self.create_input(f, "Amount (Words)", l.get("w",""), True),
            "t": self.create_input(f, "Tenure", l.get("t",""))
        }
        self.ents["ls"].append(row)
        tk.Button(f, text="Remove Loan", command=lambda r=row, fr=f.master.master: self.remove_entity(self.ents["ls"], r, fr), bg=SURFACE_CARD, fg=BTN_DANGER, font=("Segoe UI", 8, "bold"), bd=0, cursor="hand2").pack(anchor="e")
    def add_property_ui(self, p):
        idx = len(self.ents["ps"]) + 1
        f = self.create_card(self.prop_container, f"PROPERTY {idx}")
        row = {
            "adr": self.create_input(f, "Address", p.get("adr",""), True),
            "n": self.create_input(f, "North", p.get("n","")),
            "s": self.create_input(f, "South", p.get("s","")),
            "e": self.create_input(f, "East", p.get("e","")),
            "w": self.create_input(f, "West", p.get("w",""))
        }
        self.ents["ps"].append(row)
        tk.Button(f, text="Remove Property", command=lambda r=row, fr=f.master.master: self.remove_entity(self.ents["ps"], r, fr), bg=SURFACE_CARD, fg=BTN_DANGER, font=("Segoe UI", 8, "bold"), bd=0, cursor="hand2").pack(anchor="e")
    def add_witness_ui(self, w):
        idx = len(self.ents["ws"]) + 1
        f = self.create_card(self.wit_container, f"WITNESS {idx}")
        row = {
            "n": self.create_input(f, "Name", w.get("n","")),
            "r": self.create_input(f, "Relation", w.get("r","")),
            "rn": self.create_input(f, "Rel Name", w.get("rn","")),
            "adr": self.create_input(f, "Address", w.get("adr",""), True)
        }
        self.ents["ws"].append(row)
        tk.Button(f, text="Remove Witness", command=lambda r=row, fr=f.master.master: self.remove_entity(self.ents["ws"], r, fr), bg=SURFACE_CARD, fg=BTN_DANGER, font=("Segoe UI", 8, "bold"), bd=0, cursor="hand2").pack(anchor="e")
    def remove_entity(self, collection, row, frame):
        if row in collection:
            collection.remove(row)
        frame.destroy()

    def create_input(self, parent, label, value, is_long=False):
        f = tk.Frame(parent, bg=SURFACE_CARD)
        f.pack(fill="x", pady=8)
        tk.Label(f, text=label.upper(), bg=SURFACE_CARD, fg=TEXT_SECONDARY, font=("Segoe UI", 8, "bold")).pack(anchor="w")
        if is_long:
            e = tk.Text(f, bg="#F8FAFC", font=FONT_LABEL, height=3, bd=0, highlightthickness=1, highlightbackground=BORDER_COLOR, padx=10, pady=8)
            e.insert("1.0", str(value))
            e.pack(fill="x", pady=(4, 0))
            e.bind("<FocusIn>", lambda ev: e.config(highlightbackground=ACCENT_BLUE))
            e.bind("<FocusOut>", lambda ev: e.config(highlightbackground=BORDER_COLOR))
        else:
            e = tk.Entry(f, bg="#F8FAFC", bd=0, font=FONT_LABEL, highlightthickness=1, highlightbackground=BORDER_COLOR)
            e.insert(0, str(value))
            e.pack(fill="x", ipady=10, pady=(4, 0))
            e.bind("<FocusIn>", lambda ev: e.config(highlightbackground=ACCENT_BLUE))
            e.bind("<FocusOut>", lambda ev: e.config(highlightbackground=BORDER_COLOR))
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
