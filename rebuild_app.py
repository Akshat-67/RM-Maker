import re
import os

with open('app_backup.py', 'r') as f:
    code = f.read()

# 1. Imports
code = "import json\nimport time\nimport shutil\n" + code

# 2. Constants
MODERN_CONSTANTS = r'''# --- MODERN DESIGN CONSTANTS ---
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

# Legacy Compatibility
PANEL_LEFT = SURFACE_CARD
TEXT_COLOR = TEXT_PRIMARY

DEFAULT_GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or "AIzaSyDs32YIJx35FDhb9qOa3vTcWDtU-RpL5_w"
'''
code = re.sub(r'# --- DESIGN CONSTANTS ---.*?DEFAULT_GEMINI_API_KEY = .*?\n', MODERN_CONSTANTS + "\n", code, flags=re.DOTALL)

# 3. New Methods to Add
V5_METHODS = r'''
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

    def show_dashboard(self):
        self.active_case_id = None
        for w in self.root.winfo_children(): w.destroy()

        header = tk.Frame(self.root, bg=PRIMARY_NAV, height=70)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)
        tk.Label(header, text="LegalDoc Automator Dashboard", bg=PRIMARY_NAV, fg="white", font=("Segoe UI", 18, "bold"), padx=30).pack(side="left")

        main_c = tk.Frame(self.root, bg=BG_MAIN, padx=40, pady=40)
        main_c.pack(fill="both", expand=True)

        actions = tk.Frame(main_c, bg=BG_MAIN)
        actions.pack(fill="x", pady=(0, 20))
        tk.Button(actions, text="+ NEW CASE SESSION", command=self.new_case, bg=ACCENT_BLUE, fg="white", font=("Segoe UI", 11, "bold"), padx=20, pady=12, bd=0, cursor="hand2").pack(side="left")

        self.create_section_title(main_c, "ACTIVE & PENDING CASES")

        scroll_c = tk.Frame(main_c, bg=BG_MAIN)
        scroll_c.pack(fill="both", expand=True)

        canvas = tk.Canvas(scroll_c, bg=BG_MAIN, highlightthickness=0)
        sb = ttk.Scrollbar(scroll_c, orient="vertical", command=canvas.yview)
        list_f = tk.Frame(canvas, bg=BG_MAIN)

        canvas.create_window((0,0), window=list_f, anchor="nw", width=1200)
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
                try:
                    with open(path, "r") as f:
                        cases.append(json.load(f))
                except: pass
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

        tk.Button(c, text="RESUME SESSION", command=lambda: self.load_case(case['id']), bg="#EBF2FF", fg=ACCENT_BLUE, font=("Segoe UI", 9, "bold"), padx=15, pady=8, bd=0, cursor="hand2").pack(side="right", padx=10)
        tk.Button(c, text="DELETE", command=lambda: self.delete_case(case['id']), bg=SURFACE_CARD, fg=BTN_DANGER, font=("Segoe UI", 8), bd=0, cursor="hand2").pack(side="right")

    def new_case(self):
        self.active_case_id = f"case_{int(time.time())}"
        self.files = []
        self.extracted_data = {}
        self.verified_fields = set()
        self.watch_folder = None
        os.makedirs(os.path.join(self.cases_dir, self.active_case_id), exist_ok=True)
        self.setup_ui()

    def save_case(self):
        if not self.active_case_id: return
        data = self.get_context_from_ui()
        session = {
            "id": self.active_case_id,
            "borrower_name": data['bs'][0].get('n', 'New Case') if data.get('bs') else 'New Case',
            "bank": self.bank_var.get(),
            "last_updated": time.time(),
            "data": self.extracted_data, # store raw extracted data
            "verified_fields": list(self.verified_fields),
            "files": self.files,
            "watch_folder": self.watch_folder
        }
        path = os.path.join(self.cases_dir, self.active_case_id, "session.json")
        with open(path, "w") as f: json.dump(session, f)

    def load_case(self, case_id):
        path = os.path.join(self.cases_dir, case_id, "session.json")
        if not os.path.exists(path): return
        with open(path, "r") as f: session = json.load(f)
        self.active_case_id = session['id']
        self.files = session.get('files', [])
        self.extracted_data = session.get('data', {})
        self.verified_fields = set(session.get('verified_fields', []))
        self.watch_folder = session.get('watch_folder')
        self.setup_ui()
        self.bank_var.set(session.get('bank', 'ICICI'))
        self.display_data()

    def delete_case(self, case_id):
        if messagebox.askyesno("Delete Case", "Are you sure?"):
            shutil.rmtree(os.path.join(self.cases_dir, case_id))
            self.show_dashboard()

    def get_context_from_ui(self):
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
        except: return {}

    def set_watch_folder(self):
        p = filedialog.askdirectory()
        if p:
            self.watch_folder = p
            self.watch_lbl.config(text="Watching: " + os.path.basename(p))
            self.save_case()
            if not getattr(self, 'watcher_active', False):
                self.watcher_active = True
                self.run_watcher()

    def run_watcher(self):
        if not self.active_case_id or not self.watch_folder or not self.watch_var.get():
            self.root.after(10000, self.run_watcher)
            return
        try:
            new_files = []
            for f in os.listdir(self.watch_folder):
                if f.lower().endswith(('.pdf', '.jpg', '.jpeg', '.png')):
                    fp = os.path.join(self.watch_folder, f)
                    if fp not in self.files: new_files.append(fp)
            if new_files:
                for nf in new_files:
                    self.files.append(nf)
                    self.file_list.insert(tk.END, "  📄 " + os.path.basename(nf))
                self.start_process()
        except: pass
        self.root.after(10000, self.run_watcher)

    def smart_merge(self, old, new, path=""):
        if not old: return new
        if isinstance(new, dict):
            merged = old.copy() if isinstance(old, dict) else {}
            for k, v in new.items():
                p = f"{path}.{k}" if path else k
                if p in self.verified_fields: continue
                merged[k] = self.smart_merge(merged.get(k), v, p)
            return merged
        elif isinstance(new, list):
            merged = list(old) if isinstance(old, list) else []
            while len(merged) < len(new): merged.append({})
            return [self.smart_merge(merged[i], item, f"{path}.{i}") for i, item in enumerate(new)]
        return new
'''

# 4. Modified logic methods (Replacing existing ones)
MODIFIED_LOGIC = r'''
    def setup_ui(self):
        for w in self.root.winfo_children(): w.destroy()
        header = tk.Frame(self.root, bg=PRIMARY_NAV, height=70)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)
        tk.Label(header, text="LegalDoc Automator Pro", bg=PRIMARY_NAV, fg="white", font=("Segoe UI", 18, "bold"), padx=30).pack(side="left")
        tk.Button(header, text="BACK TO DASHBOARD", command=self.show_dashboard, bg=PRIMARY_NAV, fg="white", font=("Segoe UI", 8, "bold"), bd=0, padx=20, cursor="hand2").pack(side="left")
        tk.Button(header, text="SAVE PROGRESS", command=self.save_case, bg=ACCENT_BLUE, fg="white", font=("Segoe UI", 8, "bold"), bd=0, padx=20, pady=10, cursor="hand2").pack(side="left", padx=20)
        tk.Label(header, text="RM GENERATION ENGINE v5", bg=PRIMARY_NAV, fg="#94A3B8", font=("Segoe UI", 9, "bold"), padx=30).pack(side="right")

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

        self.create_section_title(self.left_p, "1. CASE SETTINGS")
        cs_card = self.create_card(self.left_p)
        tk.Label(cs_card, text="Borrower Count:", bg=SURFACE_CARD, font=FONT_HEADER, fg=TEXT_SECONDARY).pack(anchor="w")
        self.borr_var = tk.StringVar(value="Single")
        tk.Radiobutton(cs_card, text="Single Borrower", variable=self.borr_var, value="Single", bg=SURFACE_CARD, font=FONT_LABEL).pack(anchor="w")
        tk.Radiobutton(cs_card, text="Multiple Borrowers", variable=self.borr_var, value="Multiple", bg=SURFACE_CARD, font=FONT_LABEL).pack(anchor="w", pady=(0, 10))

        tk.Label(cs_card, text="Loan Account Count:", bg=SURFACE_CARD, font=FONT_HEADER, fg=TEXT_SECONDARY).pack(anchor="w")
        self.loan_var = tk.StringVar(value="1 Loan")
        tk.Radiobutton(cs_card, text="1 Loan Account", variable=self.loan_var, value="1 Loan", bg=SURFACE_CARD, font=FONT_LABEL).pack(anchor="w")
        tk.Radiobutton(cs_card, text="2 Loan Accounts", variable=self.loan_var, value="2 Loans", bg=SURFACE_CARD, font=FONT_LABEL).pack(anchor="w")
        tk.Radiobutton(cs_card, text="3+ Loan Accounts", variable=self.loan_var, value="3+ Loans", bg=SURFACE_CARD, font=FONT_LABEL).pack(anchor="w", pady=(0, 10))

        tk.Label(self.left_p, text="Select Bank:", bg=SURFACE_CARD, font=FONT_HEADER, fg=TEXT_SECONDARY).pack(anchor="w", pady=(10,0))
        banks = sorted(list(self.template_map.keys())) if self.template_map else ["ICICI"]
        self.bank_var = tk.StringVar(value=banks[0])
        self.bank_dropdown = ttk.Combobox(self.left_p, textvariable=self.bank_var, values=banks, font=FONT_LABEL, state="readonly")
        self.bank_dropdown.pack(fill="x", pady=(5, 15))

        self.create_section_title(self.left_p, "2. RM TEMPLATE")
        tm_card = self.create_card(self.left_p)
        tk.Button(tm_card, text="+ USE CUSTOM TEMPLATE DOCX", command=self.choose_template, bg="#EBF2FF", fg=ACCENT_BLUE, font=("Segoe UI", 9, "bold"), bd=0, pady=12, cursor="hand2").pack(fill="x")
        self.template_lbl = tk.Label(tm_card, text="Auto-selecting template", bg=SURFACE_CARD, fg=TEXT_SECONDARY, font=("Segoe UI", 8), wraplength=300)
        self.template_lbl.pack(pady=5)
        tk.Button(tm_card, text="Clear Custom Template", command=self.clear_template, bg=SURFACE_CARD, fg=BTN_DANGER, font=("Segoe UI", 8, "underline"), bd=0, cursor="hand2").pack()

        self.create_section_title(self.left_p, "3. UPLOAD DOCUMENTS")
        up_card = self.create_card(self.left_p)
        self.drop_zone = tk.Label(up_card, text="Drag & Drop Files Here", bg="#F8FAFC", fg=TEXT_SECONDARY, font=("Segoe UI", 10, "italic"), bd=1, relief="dash", height=4)
        self.drop_zone.pack(fill="x")
        if TkinterDnD:
            self.drop_zone.drop_target_register(DND_FILES)
            self.drop_zone.dnd_bind("<<Drop>>", self.drop_files)
        tk.Button(up_card, text="Browse Files", command=self.add_files, bg=SURFACE_CARD, fg=ACCENT_BLUE, font=("Segoe UI", 9, "bold"), bd=0, cursor="hand2").pack(pady=5)
        self.file_list = tk.Listbox(up_card, height=4, font=FONT_MONO, bd=0, highlightthickness=1, highlightbackground=BORDER_COLOR)
        self.file_list.pack(fill="x", pady=5)
        tk.Button(up_card, text="Clear All Files", command=self.clear_files, bg=SURFACE_CARD, fg=BTN_DANGER, font=("Segoe UI", 8), bd=0, cursor="hand2").pack(anchor="e")

        self.watch_var = tk.BooleanVar(value=False)
        tk.Checkbutton(up_card, text="Auto-Watch Folder", variable=self.watch_var, bg=SURFACE_CARD, font=FONT_LABEL).pack(anchor="w", pady=(10, 0))
        tk.Button(up_card, text="Set Watch Folder", command=self.set_watch_folder, bg=SURFACE_CARD, fg=ACCENT_BLUE, font=("Segoe UI", 8)).pack(anchor="w")
        self.watch_lbl = tk.Label(up_card, text="No folder watched", bg=SURFACE_CARD, fg=TEXT_SECONDARY, font=("Segoe UI", 7))
        self.watch_lbl.pack(anchor="w")

        self.create_section_title(self.left_p, "4. AI CONFIGURATION")
        ai_card = self.create_card(self.left_p)
        tk.Label(ai_card, text="Gemini API Key:", bg=SURFACE_CARD, font=FONT_LABEL).pack(anchor="w")
        self.api_key_entry = tk.Entry(ai_card, show="*", font=FONT_MONO, bd=0, highlightthickness=1, highlightbackground=BORDER_COLOR)
        self.api_key_entry.insert(0, DEFAULT_GEMINI_API_KEY)
        self.api_key_entry.pack(fill="x", ipady=8, pady=5)
        tk.Label(ai_card, text="AI Model:", bg=SURFACE_CARD, font=FONT_LABEL).pack(anchor="w", pady=(10,0))
        self.model_var = tk.StringVar(value="gemini-1.5-flash")
        self.model_dropdown = ttk.Combobox(ai_card, textvariable=self.model_var, values=["gemini-1.5-flash", "gemini-2.0-flash-exp"], font=FONT_LABEL)
        self.model_dropdown.pack(fill="x", pady=5)
        tk.Button(ai_card, text="Verify Key & Get Models", command=self.refresh_models, bg=SURFACE_CARD, fg=ACCENT_BLUE, font=("Segoe UI", 8), bd=0, cursor="hand2").pack()

        self.extract_btn = tk.Button(self.left_p, text="START AI AUTOMATION", command=self.start_process, bg=ACCENT_BLUE, fg="white", font=("Segoe UI", 12, "bold"), pady=15, bd=0, cursor="hand2")
        self.extract_btn.pack(fill="x", pady=30)
        self.status_var = tk.StringVar(value="Ready")
        self.status_lbl = tk.Label(self.left_p, textvariable=self.status_var, bg=SURFACE_CARD, fg=TEXT_SECONDARY, font=("Segoe UI", 9, "italic"))
        self.status_lbl.pack()

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

    def run_automation(self, k, m, bank, borrower_count, loan_count):
        try:
            self.root.after(0, lambda: self.status_var.set("AI is processing..."))
            new_data = DataExtractor(k).extract_with_ai(self.files, m, bank_name=bank, expected_borrowers=borrower_count, expected_loans=loan_count, expected_witnesses=2)
            if "error" in new_data: self.root.after(0, lambda: messagebox.showerror("AI Error", new_data["error"])); return
            self.extracted_data = self.smart_merge(self.extracted_data, new_data)
            self.root.after(0, self.display_data); self.root.after(0, self.save_case)
        except Exception as e: self.root.after(0, lambda msg=str(e): messagebox.showerror("AI Error", msg))
        finally:
            self.root.after(0, lambda: self.extract_btn.config(state="normal", text="START AI AUTOMATION"))
            self.root.after(0, lambda: self.status_var.set("Extraction Complete"))

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
        opt_f = tk.Frame(self.scroll_f, bg=BG_MAIN); opt_f.pack(fill="x", pady=5)
        self.h_ai_var = tk.BooleanVar(value=True); self.h_miss_var = tk.BooleanVar(value=True)
        tk.Checkbutton(opt_f, text="Highlight AI Data (Yellow)", variable=self.h_ai_var, bg=BG_MAIN, font=("Segoe UI", 8)).pack(side="left")
        tk.Checkbutton(opt_f, text="Highlight Missing (Red)", variable=self.h_miss_var, bg=BG_MAIN, font=("Segoe UI", 8)).pack(side="left", padx=20)
        tk.Button(self.scroll_f, text="VERIFIED: GENERATE FINAL RM DOCX", command=self.generate, bg=BTN_SUCCESS, fg="white", font=("Segoe UI", 13, "bold"), pady=20, bd=0, cursor="hand2").pack(fill="x", pady=40)

    def create_input(self, parent, label, value, is_long=False, field_path=None):
        f = tk.Frame(parent, bg=SURFACE_CARD); f.pack(fill="x", pady=8)
        header_f = tk.Frame(f, bg=SURFACE_CARD); header_f.pack(fill="x")
        tk.Label(header_f, text=label.upper(), bg=SURFACE_CARD, fg=TEXT_SECONDARY, font=("Segoe UI", 8, "bold")).pack(side="left")
        is_verified = field_path in self.verified_fields if field_path else True
        bg_color = "#FEF9C3" if (value and not is_verified) else "#F8FAFC"
        if is_long:
            e = tk.Text(f, bg=bg_color, font=FONT_LABEL, height=3, bd=0, highlightthickness=1, highlightbackground=BORDER_COLOR, padx=10, pady=8)
            e.insert("1.0", str(value)); e.pack(fill="x", pady=(4, 0))
        else:
            e = tk.Entry(f, bg=bg_color, bd=0, font=FONT_LABEL, highlightthickness=1, highlightbackground=BORDER_COLOR)
            e.insert(0, str(value)); e.pack(fill="x", ipady=10, pady=(4, 0))
        if field_path:
            v_btn = tk.Button(header_f, text="✓ VERIFIED" if is_verified else "MARK VERIFIED", font=("Segoe UI", 7, "bold"), bg=SURFACE_CARD, fg=BTN_SUCCESS if is_verified else ACCENT_BLUE, bd=0, cursor="hand2")
            v_btn.pack(side="right")
            def toggle_verify(p=field_path, b=v_btn, widget=e):
                if p in self.verified_fields: self.verified_fields.remove(p); b.config(text="MARK VERIFIED", fg=ACCENT_BLUE); widget.config(bg="#FEF9C3" if self.get_val(widget) else "#F8FAFC")
                else: self.verified_fields.add(p); b.config(text="✓ VERIFIED", fg=BTN_SUCCESS); widget.config(bg="#F8FAFC")
                self.save_case()
            v_btn.config(command=toggle_verify)
        e.bind("<FocusIn>", lambda ev: e.config(highlightbackground=ACCENT_BLUE)); e.bind("<FocusOut>", lambda ev: e.config(highlightbackground=BORDER_COLOR))
        return e

    def add_borrower_ui(self, b):
        idx = len(self.ents["bs"]) + 1
        f = self.create_card(self.borr_container, f"BORROWER {idx}")
        row = {"s": self.create_input(f, "Salutation", b.get("s",""), field_path=f"bs.{idx-1}.s"), "n": self.create_input(f, "Full Name", b.get("n",""), field_path=f"bs.{idx-1}.n"), "a": self.create_input(f, "Age", b.get("a",""), field_path=f"bs.{idx-1}.a"), "r": self.create_input(f, "Relation", b.get("r",""), field_path=f"bs.{idx-1}.r"), "rn": self.create_input(f, "Rel Name", b.get("rn",""), field_path=f"bs.{idx-1}.rn"), "adr": self.create_input(f, "Address", b.get("adr",""), is_long=True, field_path=f"bs.{idx-1}.adr"), "id": self.create_input(f, "Aadhar/ID", b.get("id",""), field_path=f"bs.{idx-1}.id")}
        self.ents["bs"].append(row)
        tk.Button(f, text="Remove", command=lambda r=row, fr=f.master.master: self.remove_entity(self.ents["bs"], r, fr), bg=SURFACE_CARD, fg=BTN_DANGER, font=("Segoe UI", 8, "bold"), bd=0).pack(anchor="e")

    def add_loan_ui(self, l):
        idx = len(self.ents["ls"]) + 1
        f = self.create_card(self.loan_container, f"LOAN ACCOUNT {idx}")
        row = {"n": self.create_input(f, "LAN No", l.get("n",""), field_path=f"ls.{idx-1}.n"), "a": self.create_input(f, "Amount (Figures)", l.get("a",""), field_path=f"ls.{idx-1}.a"), "w": self.create_input(f, "Amount (Words)", l.get("w",""), is_long=True, field_path=f"ls.{idx-1}.w"), "t": self.create_input(f, "Tenure", l.get("t",""), field_path=f"ls.{idx-1}.t")}
        self.ents["ls"].append(row)
        tk.Button(f, text="Remove", command=lambda r=row, fr=f.master.master: self.remove_entity(self.ents["ls"], r, fr), bg=SURFACE_CARD, fg=BTN_DANGER, font=("Segoe UI", 8, "bold"), bd=0).pack(anchor="e")

    def add_property_ui(self, p):
        idx = len(self.ents["ps"]) + 1
        f = self.create_card(self.prop_container, f"PROPERTY {idx}")
        row = {"adr": self.create_input(f, "Address", p.get("adr",""), is_long=True, field_path=f"ps.{idx-1}.adr"), "n": self.create_input(f, "North", p.get("n",""), field_path=f"ps.{idx-1}.n"), "s": self.create_input(f, "South", p.get("s",""), field_path=f"ps.{idx-1}.s"), "e": self.create_input(f, "East", p.get("e",""), field_path=f"ps.{idx-1}.e"), "w": self.create_input(f, "West", p.get("w",""), field_path=f"ps.{idx-1}.w")}
        self.ents["ps"].append(row)
        tk.Button(f, text="Remove", command=lambda r=row, fr=f.master.master: self.remove_entity(self.ents["ps"], r, fr), bg=SURFACE_CARD, fg=BTN_DANGER, font=("Segoe UI", 8, "bold"), bd=0).pack(anchor="e")

    def add_witness_ui(self, w):
        idx = len(self.ents["ws"]) + 1
        f = self.create_card(self.wit_container, f"WITNESS {idx}")
        row = {"n": self.create_input(f, "Name", w.get("n",""), field_path=f"ws.{idx-1}.n"), "r": self.create_input(f, "Relation", w.get("r",""), field_path=f"ws.{idx-1}.r"), "rn": self.create_input(f, "Rel Name", w.get("rn",""), field_path=f"ws.{idx-1}.rn"), "adr": self.create_input(f, "Address", w.get("adr",""), is_long=True, field_path=f"ws.{idx-1}.adr")}
        self.ents["ws"].append(row)
        tk.Button(f, text="Remove", command=lambda r=row, fr=f.master.master: self.remove_entity(self.ents["ws"], r, fr), bg=SURFACE_CARD, fg=BTN_DANGER, font=("Segoe UI", 8, "bold"), bd=0).pack(anchor="e")

    def generate(self):
        bank, borr, loan = self.bank_var.get(), self.borr_var.get(), self.loan_var.get()
        t_path = self.custom_template_path.get().strip()
        if not t_path:
            try: t_path = self.template_map[bank][borr][loan]
            except KeyError: messagebox.showerror("Error", f"No template found for {bank}"); return
        if not os.path.exists(t_path): messagebox.showerror("Error", "Template not found"); return
        try:
            c = self.get_context_from_ui()
            sp = filedialog.asksaveasfilename(defaultextension=".docx", initialfile=f"RM_{bank}.docx")
            if sp:
                TemplateProcessor(t_path).generate(c, sp, highlight_ai=self.h_ai_var.get(), highlight_missing=self.h_miss_var.get(), verified_fields=self.verified_fields)
                messagebox.showinfo("Success", f"RM Generated successfully at:\n{sp}")
        except Exception as e: messagebox.showerror("Generation Error", str(e))
'''

# 5. ASSEMBLE (Final)
logic_m = ['discover_templates', 'docx_has_placeholders', 'refresh_models', 'add_files', 'clear_files', 'add_file_path', 'drop_files', 'choose_template', 'clear_template', 'start_process', 'expected_borrower_count', 'expected_loan_count', 'enforce_case_counts', 'get_extraction_warnings', 'remove_entity', 'get_val', 'enforce_context_counts']

out = HEADER + CONSTANTS + "class LawApp:\n" + HELPERS + NEW_INIT + NEW_SETUP_UI
for m in logic_m: out += get_method_body(orig_code, m) + "\n"
out += V5_METHODS + MODIFIED_LOGIC
out += "\nif __name__ == '__main__':\n    root = TkinterDnD.Tk() if TkinterDnD else tk.Tk()\n    LawApp(root)\n    root.mainloop()\n"

with open('app.py', 'w') as f:
    f.write(out)
"
python3 -m py_compile app.py
