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
BG_MAIN = "#F8FAFC"
SURFACE_CARD = "#FFFFFF"
ACCENT_BLUE = "#2563EB"
BTN_SUCCESS = "#10B981"
BTN_DANGER = "#EF4444"
BORDER_COLOR = "#E2E8F0"
PRIMARY_NAV = "#0F172A"
TEXT_PRIMARY = "#1E293B"
TEXT_SECONDARY = "#64748B"
FONT_DISPLAY = ("Segoe UI", 14, "bold")
TEXT_PRIMARY = "#3C4043"

FONT_HEADER = ("Segoe UI", 12, "bold")
FONT_LABEL = ("Segoe UI", 10)
FONT_MONO = ("Consolas", 10)
DEFAULT_GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or "AIzaSyDs32YIJx35FDhb9qOa3vTcWDtU-RpL5_w"

class LawApp:
    def __init__(self, root):
        self.root = root
        self.root.title("LegalDoc Automator Pro v5")
        self.root.geometry("1400x980")
        self.root.configure(bg=BG_MAIN)

        # Session State
        self.active_case_id = None
        self.cases_dir = "cases"
        os.makedirs(self.cases_dir, exist_ok=True)

        self.files = []
        self.extracted_data = {}
        self.verified_fields = set()

        self.template_map = {}
        self.custom_template_path = tk.StringVar(value="")

        self.discover_templates()
        self.show_dashboard()
        self.watch_folder = None

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
        left_container = tk.Frame(main_c, bg=SURFACE_CARD, width=480, highlightbackground=BORDER_COLOR, highlightthickness=1)
        left_container.pack(side="left", fill="y")
        left_container.pack_propagate(False)

        left_canvas = tk.Canvas(left_container, bg=SURFACE_CARD, highlightthickness=0)
        left_sb = ttk.Scrollbar(left_container, orient="vertical", command=left_canvas.yview)
        left_p = tk.Frame(left_canvas, bg=SURFACE_CARD, padx=20, pady=20)

        left_canvas.create_window((0,0), window=left_p, anchor="nw", width=460)
        left_canvas.configure(yscrollcommand=left_sb.set)

        left_canvas.pack(side="left", fill="both", expand=True)
        left_sb.pack(side="right", fill="y")
        left_p.bind("<Configure>", lambda e: left_canvas.configure(scrollregion=left_canvas.bbox("all")))

        # 1. Case Settings
        sec1 = tk.LabelFrame(left_p, text=" 1. CASE SETTINGS ", font=FONT_HEADER, bg=SURFACE_CARD, fg=ACCENT_BLUE, padx=15, pady=15)
        sec1.pack(fill="x", pady=(0,15))

        tk.Label(left_p, text="Select Bank:", font=FONT_LABEL, bg=SURFACE_CARD).pack(anchor="w")
        banks = list(self.template_map.keys()) if self.template_map else ["ICICI"]
        self.bank_var = tk.StringVar(value=banks[0])
        self.bank_dropdown = ttk.Combobox(left_p, textvariable=self.bank_var, values=banks, font=FONT_LABEL)
        self.bank_dropdown.pack(fill="x", pady=(5, 15))

        tk.Label(sec1, text="Borrower Count:", font=FONT_LABEL, bg=SURFACE_CARD).pack(anchor="w")
        self.borr_var = tk.StringVar(value="Single")
        tk.Radiobutton(sec1, text="Single Borrower", variable=self.borr_var, value="Single", bg=SURFACE_CARD, font=FONT_LABEL).pack(anchor="w")
        tk.Radiobutton(sec1, text="Multiple Borrowers", variable=self.borr_var, value="Multiple", bg=SURFACE_CARD, font=FONT_LABEL).pack(anchor="w", pady=(0, 10))

        tk.Label(sec1, text="Loan Account Count:", font=FONT_LABEL, bg=SURFACE_CARD).pack(anchor="w")
        self.loan_var = tk.StringVar(value="1 Loan")
        tk.Radiobutton(sec1, text="1 Loan Account", variable=self.loan_var, value="1 Loan", bg=SURFACE_CARD, font=FONT_LABEL).pack(anchor="w")
        tk.Radiobutton(sec1, text="2 Loan Accounts", variable=self.loan_var, value="2 Loans", bg=SURFACE_CARD, font=FONT_LABEL).pack(anchor="w")
        tk.Radiobutton(sec1, text="3+ Loan Accounts", variable=self.loan_var, value="3+ Loans", bg=SURFACE_CARD, font=FONT_LABEL).pack(anchor="w")

        # 2. Template Upload
        sec_template = tk.LabelFrame(left_p, text=" 2. RM TEMPLATE ", font=FONT_HEADER, bg=SURFACE_CARD, fg=ACCENT_BLUE, padx=15, pady=15)
        sec_template.pack(fill="x", pady=15)
        tk.Button(sec_template, text="+ USE CUSTOM TEMPLATE DOCX", command=self.choose_template, bg="#E8F0FE", fg=ACCENT_BLUE, font=("Segoe UI", 10, "bold"), bd=0, pady=10, cursor="hand2").pack(fill="x", pady=(0, 8))
        self.template_lbl = tk.Label(sec_template, text="Auto-selecting from templates folder", bg=SURFACE_CARD, fg="#5F6368", font=("Segoe UI", 9), wraplength=390, justify="left")
        self.template_lbl.pack(fill="x", anchor="w")
        tk.Button(sec_template, text="Clear Custom Template", command=self.clear_template, bg="#FFFFFF", fg=BTN_DANGER, bd=1, relief="flat", font=("Segoe UI", 9)).pack(fill="x", pady=(8, 0))

        # 3. Document Upload
        sec2 = tk.LabelFrame(left_p, text=" 3. UPLOAD DOCUMENTS ", font=FONT_HEADER, bg=SURFACE_CARD, fg=ACCENT_BLUE, padx=15, pady=15)
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
        sec3 = tk.LabelFrame(left_p, text=" 4. AI CONFIGURATION ", font=FONT_HEADER, bg=SURFACE_CARD, fg=ACCENT_BLUE, padx=15, pady=15)
        sec3.pack(fill="x", pady=15)
        tk.Label(sec3, text="Gemini API Key:", font=("Segoe UI", 9), bg=SURFACE_CARD).pack(anchor="w")
        self.api_key_entry = tk.Entry(sec3, show="*", bg="#F1F3F4", bd=0, font=FONT_MONO, highlightthickness=1, highlightbackground=BORDER_COLOR)
        self.api_key_entry.insert(0, DEFAULT_GEMINI_API_KEY)
        self.api_key_entry.pack(fill="x", ipady=8, pady=5)

        tk.Label(sec3, text="Select AI Model:", font=("Segoe UI", 9), bg=SURFACE_CARD).pack(anchor="w", pady=(8,0))
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
        tk.Label(top_bar, text="VERIFICATION & EDITING", font=FONT_HEADER, bg=BG_MAIN, fg=TEXT_PRIMARY).pack(side="left")
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
            self.root.after(0, lambda: self.status_var.set("AI is processing documents..."))
            new_data = DataExtractor(k).extract_with_ai(
                self.files,
                m,
                bank_name=bank,
                expected_borrowers=borrower_count,
                expected_loans=loan_count,
                expected_witnesses=2,
            )

            if "error" in new_data:
                 self.root.after(0, lambda: messagebox.showerror("AI Error", new_data["error"]))
                 return

            # SMART MERGE: Keep verified fields, update others
            self.extracted_data = self.smart_merge(self.extracted_data, new_data)

            self.root.after(0, self.display_data)
            self.root.after(0, self.save_case)
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda msg=error_msg: messagebox.showerror("AI Error", msg))
        finally:
            self.root.after(0, lambda: self.extract_btn.config(state="normal", text="START AI AUTOMATION"))
            self.root.after(0, lambda: self.status_var.set("Extraction Complete"))

    def smart_merge(self, old, new, path=""):
        if not old: return new
        if isinstance(new, dict):
            merged = old.copy() if isinstance(old, dict) else {}
            for k, v in new.items():
                new_path = f"{path}.{k}" if path else k
                if new_path in self.verified_fields: continue
                merged[k] = self.smart_merge(merged.get(k), v, new_path)
            return merged
        elif isinstance(new, list):
            # For lists, we merge by index
            merged = list(old) if isinstance(old, list) else []
            while len(merged) < len(new): merged.append({})
            return [self.smart_merge(merged[i], item, f"{path}.{i}") for i, item in enumerate(new)]
        else:
            return new
    def display_data(self):
        for w in self.scroll_f.winfo_children(): w.destroy()
        if not self.extracted_data: return
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
        self.ents["rd"] = self.create_input(dates_card, "RM Execution Date", d.get("rd", ""), field_path="rd")
        self.ents["ad"] = self.create_input(dates_card, "Loan Agreement Date", d.get("ad", ""), field_path="ad")

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
            "n": self.create_input(bsign_card, "Name", sig.get("n", ""), field_path="bsign.n"),
            "r": self.create_input(bsign_card, "Relation", sig.get("r", ""), field_path="bsign.r"),
            "rn": self.create_input(bsign_card, "Rel Name", sig.get("rn", ""), field_path="bsign.rn")
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

        # Draft Options
        opt_f = tk.Frame(self.scroll_f, bg=BG_MAIN)
        opt_f.pack(fill="x", pady=5)
        self.h_ai_var = tk.BooleanVar(value=True)
        self.h_miss_var = tk.BooleanVar(value=True)
        tk.Checkbutton(opt_f, text="Highlight AI Data (Yellow)", variable=self.h_ai_var, bg=BG_MAIN, font=("Segoe UI", 8)).pack(side="left")
        tk.Checkbutton(opt_f, text="Highlight Missing (Red)", variable=self.h_miss_var, bg=BG_MAIN, font=("Segoe UI", 8)).pack(side="left", padx=20)
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

    def add_borrower_ui(self, data_obj):
        idx = len(self.ents["bs"]) + 1
        f = self.create_card(self.br_container, f"BS {idx}")
        row = {
            "s": self.create_input(f, "s", data_obj.get("s",""), is_long=False, field_path=f"bs.{idx-1}.s"),
            "n": self.create_input(f, "n", data_obj.get("n",""), is_long=False, field_path=f"bs.{idx-1}.n"),
            "a": self.create_input(f, "a", data_obj.get("a",""), is_long=False, field_path=f"bs.{idx-1}.a"),
            "r": self.create_input(f, "r", data_obj.get("r",""), is_long=False, field_path=f"bs.{idx-1}.r"),
            "rn": self.create_input(f, "rn", data_obj.get("rn",""), is_long=False, field_path=f"bs.{idx-1}.rn"),
            "adr": self.create_input(f, "adr", data_obj.get("adr",""), is_long=True, field_path=f"bs.{idx-1}.adr"),
            "id": self.create_input(f, "id", data_obj.get("id",""), is_long=False, field_path=f"bs.{idx-1}.id")

        }
        self.ents["bs"].append(row)
        tk.Button(f, text="Remove", command=lambda r=row, fr=f.master.master: self.remove_entity(self.ents["bs"], r, fr), bg=SURFACE_CARD, fg=BTN_DANGER, font=("Segoe UI", 8, "bold"), bd=0, cursor="hand2").pack(anchor="e")
    def add_loan_ui(self, data_obj):
        idx = len(self.ents["ls"]) + 1
        f = self.create_card(self.lr_container, f"LS {idx}")
        row = {
            "n": self.create_input(f, "n", data_obj.get("n",""), is_long=False, field_path=f"ls.{idx-1}.n"),
            "a": self.create_input(f, "a", data_obj.get("a",""), is_long=False, field_path=f"ls.{idx-1}.a"),
            "w": self.create_input(f, "w", data_obj.get("w",""), is_long=False, field_path=f"ls.{idx-1}.w"),
            "t": self.create_input(f, "t", data_obj.get("t",""), is_long=False, field_path=f"ls.{idx-1}.t")

        }
        self.ents["ls"].append(row)
        tk.Button(f, text="Remove", command=lambda r=row, fr=f.master.master: self.remove_entity(self.ents["ls"], r, fr), bg=SURFACE_CARD, fg=BTN_DANGER, font=("Segoe UI", 8, "bold"), bd=0, cursor="hand2").pack(anchor="e")
    def add_property_ui(self, data_obj):
        idx = len(self.ents["ps"]) + 1
        f = self.create_card(self.pr_container, f"PS {idx}")
        row = {
            "adr": self.create_input(f, "adr", data_obj.get("adr",""), is_long=True, field_path=f"ps.{idx-1}.adr"),
            "n": self.create_input(f, "n", data_obj.get("n",""), is_long=False, field_path=f"ps.{idx-1}.n"),
            "s": self.create_input(f, "s", data_obj.get("s",""), is_long=False, field_path=f"ps.{idx-1}.s"),
            "e": self.create_input(f, "e", data_obj.get("e",""), is_long=False, field_path=f"ps.{idx-1}.e"),
            "w": self.create_input(f, "w", data_obj.get("w",""), is_long=False, field_path=f"ps.{idx-1}.w")

        }
        self.ents["ps"].append(row)
        tk.Button(f, text="Remove", command=lambda r=row, fr=f.master.master: self.remove_entity(self.ents["ps"], r, fr), bg=SURFACE_CARD, fg=BTN_DANGER, font=("Segoe UI", 8, "bold"), bd=0, cursor="hand2").pack(anchor="e")
    def add_witness_ui(self, data_obj):
        idx = len(self.ents["ws"]) + 1
        f = self.create_card(self.wr_container, f"WS {idx}")
        row = {
            "n": self.create_input(f, "n", data_obj.get("n",""), is_long=False, field_path=f"ws.{idx-1}.n"),
            "r": self.create_input(f, "r", data_obj.get("r",""), is_long=False, field_path=f"ws.{idx-1}.r"),
            "rn": self.create_input(f, "rn", data_obj.get("rn",""), is_long=False, field_path=f"ws.{idx-1}.rn"),
            "adr": self.create_input(f, "adr", data_obj.get("adr",""), is_long=True, field_path=f"ws.{idx-1}.adr")

        }
        self.ents["ws"].append(row)
        tk.Button(f, text="Remove", command=lambda r=row, fr=f.master.master: self.remove_entity(self.ents["ws"], r, fr), bg=SURFACE_CARD, fg=BTN_DANGER, font=("Segoe UI", 8, "bold"), bd=0, cursor="hand2").pack(anchor="e")
    def remove_entity(self, collection, row, frame):
        if row in collection:
            collection.remove(row)
        frame.destroy()

    def create_input(self, parent, label, value, is_long=False, field_path=None):
        f = tk.Frame(parent, bg=SURFACE_CARD)
        f.pack(fill="x", pady=8)
        header_f = tk.Frame(f, bg=SURFACE_CARD)
        header_f.pack(fill="x")
        tk.Label(header_f, text=label.upper(), bg=SURFACE_CARD, fg=TEXT_SECONDARY, font=("Segoe UI", 8, "bold")).pack(side="left")
        is_verified = field_path in self.verified_fields if field_path else True
        bg_color = "#FEF9C3" if (value and not is_verified) else "#F8FAFC"
        if is_long:
            e = tk.Text(f, bg=bg_color, font=FONT_LABEL, height=3, bd=0, highlightthickness=1, highlightbackground=BORDER_COLOR, padx=10, pady=8)
            e.insert("1.0", str(value))
            e.pack(fill="x", pady=(4, 0))
        else:
            e = tk.Entry(f, bg=bg_color, bd=0, font=FONT_LABEL, highlightthickness=1, highlightbackground=BORDER_COLOR)
            e.insert(0, str(value))
            e.pack(fill="x", ipady=10, pady=(4, 0))
        if field_path:
            v_btn = tk.Button(header_f, text="✓ VERIFIED" if is_verified else "MARK VERIFIED", font=("Segoe UI", 7, "bold"), bg=SURFACE_CARD, fg=BTN_SUCCESS if is_verified else ACCENT_BLUE, bd=0, cursor="hand2")
            v_btn.pack(side="right")
            def toggle_verify(p=field_path, b=v_btn, widget=e):
                if p in self.verified_fields: self.verified_fields.remove(p); b.config(text="MARK VERIFIED", fg=ACCENT_BLUE); widget.config(bg="#FEF9C3" if self.get_val(widget) else "#F8FAFC")
                else: self.verified_fields.add(p); b.config(text="✓ VERIFIED", fg=BTN_SUCCESS); widget.config(bg="#F8FAFC")
                self.save_case()
            v_btn.config(command=toggle_verify)
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
                TemplateProcessor(t_path).generate(c, sp, highlight_ai=self.h_ai_var.get(), highlight_missing=self.h_miss_var.get(), verified_fields=self.verified_fields)
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


    def show_dashboard(self):
        self.active_case_id = None
        """Display the central case management view."""
        for w in self.root.winfo_children(): w.destroy()

        # Header
        header = tk.Frame(self.root, bg=PRIMARY_NAV, height=70)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)
        tk.Label(header, text="LegalDoc Automator Dashboard", bg=PRIMARY_NAV, fg="white", font=("Segoe UI", 18, "bold"), padx=30).pack(side="left")

        main_c = tk.Frame(self.root, bg=BG_MAIN, padx=40, pady=40)
        main_c.pack(fill="both", expand=True)

        # Actions Row
        actions = tk.Frame(main_c, bg=BG_MAIN)
        actions.pack(fill="x", pady=(0, 20))
        tk.Button(actions, text="+ NEW CASE SESSION", command=self.new_case, bg=ACCENT_BLUE, fg="white", font=("Segoe UI", 11, "bold"), padx=20, pady=12, bd=0, cursor="hand2").pack(side="left")

        # Case List Area
        self.create_section_title(main_c, "ACTIVE & PENDING CASES")

        scroll_c = tk.Frame(main_c, bg=BG_MAIN)
        scroll_c.pack(fill="both", expand=True)

        canvas = tk.Canvas(scroll_c, bg=BG_MAIN, highlightthickness=0)
        sb = ttk.Scrollbar(scroll_c, orient="vertical", command=canvas.yview)
        list_f = tk.Frame(canvas, bg=BG_MAIN)

        canvas.create_window((0,0), window=list_f, anchor="nw", width=1300)
        canvas.configure(yscrollcommand=sb.set)
        list_f.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        cases = self.list_cases()
        if not cases:
            tk.Label(list_f, text="No active cases found. Start a new case to begin.", bg=BG_MAIN, fg=TEXT_SECONDARY, font=FONT_LABEL, pady=40).pack()
        else:
            for case in cases:
                self.add_case_row(list_f, case)

    def list_cases(self):
        cases = []
        if not os.path.exists(self.cases_dir): return []
        for d in os.listdir(self.cases_dir):
            path = os.path.join(self.cases_dir, d, "session.json")
            if os.path.exists(path):
                with open(path, "r") as f:
                    cases.append(json.load(f))
        return sorted(cases, key=lambda x: x.get('last_updated', 0), reverse=True)

    def add_case_row(self, parent, case):
        c = self.create_card(parent)
        name = case.get('borrower_name', 'Unnamed Case') or 'Unnamed Case'
        bank = case.get('bank', 'Not Selected')
        updated = time.strftime('%d %b, %H:%M', time.localtime(case.get('last_updated', 0)))

        left = tk.Frame(c, bg=SURFACE_CARD)
        left.pack(side="left", fill="x", expand=True)

        tk.Label(left, text=name, font=FONT_DISPLAY, bg=SURFACE_CARD, fg=TEXT_PRIMARY, anchor="w").pack(fill="x")
        tk.Label(left, text=f"{bank} | Updated: {updated}", font=FONT_LABEL, bg=SURFACE_CARD, fg=TEXT_SECONDARY, anchor="w").pack(fill="x")

        # Simple Progress Indicator
        prog_f = tk.Frame(c, bg=SURFACE_CARD)
        prog_f.pack(side="left", padx=40)

        stats = case.get('stats', {})
        for label, val in [("KYC", stats.get('kyc')), ("Loan", stats.get('loan')), ("Legal", stats.get('legal'))]:
            color = BTN_SUCCESS if val else "#E2E8F0"
            f = tk.Frame(prog_f, bg=color, width=80, height=25)
            f.pack(side="left", padx=5)
            f.pack_propagate(False)
            tk.Label(f, text=label, bg=color, fg="white" if val else TEXT_SECONDARY, font=("Segoe UI", 8, "bold")).pack(expand=True)

        tk.Button(c, text="RESUME SESSION", command=lambda: self.load_case(case['id']), bg="#EBF2FF", fg=ACCENT_BLUE, font=("Segoe UI", 9, "bold"), padx=15, pady=8, bd=0, cursor="hand2").pack(side="right", padx=10)
        tk.Button(c, text="DELETE", command=lambda: self.delete_case(case['id']), bg=SURFACE_CARD, fg=BTN_DANGER, font=("Segoe UI", 8), bd=0, cursor="hand2").pack(side="right")

    def new_case(self):
        self.active_case_id = f"case_{int(time.time())}"
        self.files = []
        self.extracted_data = {}
        self.verified_fields = set()
        os.makedirs(os.path.join(self.cases_dir, self.active_case_id), exist_ok=True)
        self.setup_ui()

    def save_case(self):
        if not self.active_case_id: return

        # Gather current data from UI
        data = self.get_context_from_ui()

        session = {
            "id": self.active_case_id,
            "borrower_name": data['bs'][0].get('n', 'New Case'),
            "bank": self.bank_var.get(),
            "last_updated": time.time(),
            "data": data,
            "verified_fields": list(self.verified_fields),
            "files": self.files,
            "watch_folder": self.watch_folder,
            "stats": {
                "kyc": bool(data['bs'][0].get('id')),
                "loan": bool(data['ls'][0].get('a')),
                "legal": bool(data['rd'])
            }
        }

        path = os.path.join(self.cases_dir, self.active_case_id, "session.json")
        with open(path, "w") as f:
            json.dump(session, f)

        self.status_var.set("Case Saved Successfully")

    def load_case(self, case_id):
        path = os.path.join(self.cases_dir, case_id, "session.json")
        if not os.path.exists(path): return

        with open(path, "r") as f:
            session = json.load(f)

        self.active_case_id = session['id']
        self.files = session.get('files', [])
        self.watch_folder = session.get("watch_folder")
        if self.watch_folder: self.watch_lbl.config(text="Watching: " + os.path.basename(self.watch_folder))
        self.extracted_data = session.get('data', {})
        self.verified_fields = set(session.get('verified_fields', []))

        self.setup_ui()
        self.bank_var.set(session.get('bank', 'ICICI'))
        self.display_data()

    def delete_case(self, case_id):
        if messagebox.askyesno("Delete Case", "Are you sure you want to permanently delete this case and all its files?"):
            shutil.rmtree(os.path.join(self.cases_dir, case_id))
            self.show_dashboard()

    def get_context_from_ui(self):
        """Extract data from UI fields (ents)."""
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
            return self.enforce_context_counts(c)
        except:
            return {}


    def set_watch_folder(self):
        path = filedialog.askdirectory()
        if path:
            self.watch_folder = path
            self.watch_lbl.config(text="Watching: " + os.path.basename(path))
            self.save_case()
            if not getattr(self, "watcher_active", False):
                self.watcher_active = True
                self.run_watcher()

    def run_watcher(self):
        if not self.active_case_id or not self.watch_folder or not self.watch_var.get():
            self.root.after(10000, self.run_watcher)
            return
        try:
            new_files = []
            for f in os.listdir(self.watch_folder):
                if f.lower().endswith((".pdf", ".jpg", ".jpeg", ".png")):
                    full_path = os.path.join(self.watch_folder, f)
                    if full_path not in self.files: new_files.append(full_path)
            if new_files:
                self.status_var.set("Detected " + str(len(new_files)) + " new files! Starting extraction...")
                for nf in new_files:
                    self.files.append(nf)
                    self.file_list.insert(tk.END, "  📄 " + os.path.basename(nf))
                self.start_process()
        except: pass
        self.root.after(10000, self.run_watcher)

if __name__ == "__main__":
    root = TkinterDnD.Tk() if TkinterDnD else tk.Tk()
    LawApp(root)
    root.mainloop()
