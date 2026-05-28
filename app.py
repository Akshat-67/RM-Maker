import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import threading
import re
import json
import time
import shutil
from extractor import DataExtractor
from processor import TemplateProcessor

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
except ImportError:
    DND_FILES = None
    TkinterDnD = None

# --- MODERN DESIGN CONSTANTS ---
BG_MAIN = "#F8FAFC"
SURFACE_CARD = "#FFFFFF"
PRIMARY_NAV = "#0F172A"
ACCENT_BLUE = "#1565C0"       # Used for buttons/backgrounds  
ACCENT_BLUE_LIGHT = "#000000" # Pure black for max contrast on white backgrounds
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
        self.watch_folder = None
        self.watcher_active = False

        self.template_map = {}          # {BANK: {B_COUNT: {L_COUNT: filepath}}}
        self.bank_folders = []          # list of bank subfolder names
        self.custom_template_path = tk.StringVar(value="")

        self.discover_templates()
        self.available_models = []
        self.model_var = tk.StringVar(value="gemini-1.5-flash")
        self.show_dashboard()
        # Auto-fetch models in background
        threading.Thread(target=self._auto_fetch_models, daemon=True).start()

    def _auto_fetch_models(self):
        """Fetch available Gemini models on startup."""
        try:
            extractor = DataExtractor(DEFAULT_GEMINI_API_KEY)
            models = extractor.get_available_models()
            if models:
                self.available_models = models
                preferred = [m for m in models if "gemini-2.5-flash" in m.lower() or "gemini-2.0-flash" in m.lower()]
                best = preferred[0] if preferred else models[0]
                self.model_var.set(best)
                self.root.after(0, lambda: self._refresh_dropdowns())
        except Exception:
            pass

    def _refresh_dropdowns(self):
        """Refresh model dropdowns in any open UI."""
        if hasattr(self, 'model_dropdown') and self.model_dropdown:
            self.model_dropdown['values'] = self.available_models
            if self.model_var.get() not in self.available_models:
                self.model_var.set(self.available_models[0] if self.available_models else "gemini-1.5-flash")
        if hasattr(self, 'api_key_entry') and self.api_key_entry:
            self.api_key_entry.delete(0, tk.END)
            self.api_key_entry.insert(0, DEFAULT_GEMINI_API_KEY)

    def _refresh_models_click(self):
        """Manual refresh button handler."""
        self._refresh_dropdowns()
        messagebox.showinfo("Models", f"Using: {self.model_var.get()}")

    # ===================== UI HELPERS =====================

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
            v_btn = tk.Button(header_f, text="✓ VERIFIED" if is_verified else "MARK VERIFIED",
                             font=("Segoe UI", 7, "bold"), bg=SURFACE_CARD,
                             fg=BTN_SUCCESS if is_verified else ACCENT_BLUE_LIGHT, bd=0, cursor="hand2")
            v_btn.pack(side="right")
            def toggle_verify(p=field_path, b=v_btn, widget=e):
                if p in self.verified_fields:
                    self.verified_fields.remove(p)
                    b.config(text="MARK VERIFIED", fg=ACCENT_BLUE_LIGHT)
                    widget.config(bg="#FEF9C3" if self.get_val(widget) else "#F8FAFC")
                else:
                    self.verified_fields.add(p)
                    b.config(text="✓ VERIFIED", fg=BTN_SUCCESS)
                    widget.config(bg="#F8FAFC")
                self.save_case(show_feedback=False)
            v_btn.config(command=toggle_verify)

        # Auto-save when user edits a field
        def on_field_edit(*args):
            self.root.after(500, self._debounced_save)
        e.bind("<KeyRelease>", on_field_edit)

        e.bind("<FocusIn>", lambda ev: e.config(highlightbackground=ACCENT_BLUE))
        e.bind("<FocusOut>", lambda ev: e.config(highlightbackground=BORDER_COLOR))
        return e

    def _enable_mousewheel(self, canvas):
        """Bind mousewheel/trackpad scrolling to a canvas."""
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        def _on_shift_mousewheel(event):
            canvas.xview_scroll(int(-1 * (event.delta / 120)), "units")
        # Windows
        canvas.bind_all("<MouseWheel>", _on_mousewheel, add="+")
        # Linux
        canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-3, "units"), add="+")
        canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(3, "units"), add="+")

    def _debounced_save(self):
        self.save_case(show_feedback=False)

    # ===================== DASHBOARD =====================

    def show_dashboard(self):
        self.active_case_id = None
        for w in self.root.winfo_children(): w.destroy()

        header = tk.Frame(self.root, bg=PRIMARY_NAV, height=70)
        header.pack(fill="x", side="top"); header.pack_propagate(False)
        tk.Label(header, text="LegalDoc Automator Dashboard", bg=PRIMARY_NAV, fg="white", font=("Segoe UI", 18, "bold"), padx=30).pack(side="left")

        main_c = tk.Frame(self.root, bg=BG_MAIN, padx=40, pady=40); main_c.pack(fill="both", expand=True)

        actions = tk.Frame(main_c, bg=BG_MAIN); actions.pack(fill="x", pady=(0, 20))
        tk.Button(actions, text="+ NEW CASE SESSION", command=self.new_case, bg=ACCENT_BLUE, fg="white", font=("Segoe UI", 11, "bold"), padx=20, pady=12, bd=0, cursor="hand2").pack(side="left")

        self.create_section_title(main_c, "ACTIVE & PENDING CASES")

        scroll_c = tk.Frame(main_c, bg=BG_MAIN); scroll_c.pack(fill="both", expand=True)
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
                self.add_dashboard_row(list_f, case)

    def add_dashboard_row(self, parent, case):
        c = self.create_card(parent)
        name = case.get('borrower_name', 'Unnamed Case') or 'Unnamed Case'
        bank = case.get('bank', 'Not Selected')
        updated = time.strftime('%d %b, %H:%M', time.localtime(case.get('last_updated', 0)))

        left = tk.Frame(c, bg=SURFACE_CARD)
        left.pack(side="left", fill="x", expand=True)

        tk.Label(left, text=name, font=FONT_DISPLAY, bg=SURFACE_CARD, fg=TEXT_PRIMARY, anchor="w").pack(fill="x")
        tk.Label(left, text=f"{bank} | Updated: {updated}", font=FONT_LABEL, bg=SURFACE_CARD, fg=TEXT_SECONDARY, anchor="w").pack(fill="x")

        tk.Button(c, text="RESUME SESSION", command=lambda: self.load_case(case['id']), bg=ACCENT_BLUE, fg="white", font=("Segoe UI", 9, "bold"), padx=15, pady=8, bd=0, cursor="hand2").pack(side="right", padx=10)
        tk.Button(c, text="DELETE", command=lambda: self.delete_case(case['id']), bg=SURFACE_CARD, fg=BTN_DANGER, font=("Segoe UI", 8), bd=0, cursor="hand2").pack(side="right")

    def list_cases(self):
        cases = []
        if not os.path.exists(self.cases_dir): return []
        for d in os.listdir(self.cases_dir):
            path = os.path.join(self.cases_dir, d, "session.json")
            if os.path.exists(path):
                try:
                    with open(path, "r") as f: cases.append(json.load(f))
                except: pass
        return sorted(cases, key=lambda x: x.get('last_updated', 0), reverse=True)

    def new_case(self):
        self.active_case_id = f"case_{int(time.time())}"
        self.files, self.extracted_data, self.verified_fields, self.watch_folder = [], {}, set(), None
        os.makedirs(os.path.join(self.cases_dir, self.active_case_id), exist_ok=True)
        self.setup_ui()

    def save_case(self, show_feedback=True):
        """Save the current UI state to session file.
        Also updates self.extracted_data with the latest values from the UI fields.
        """
        if not self.active_case_id: return

        # Read current values from the UI into extracted_data
        ui_data = self._read_ui_to_dict()
        if ui_data:
            self.extracted_data = ui_data

        data = self.get_context_from_ui()
        session = {
            "id": self.active_case_id,
            "borrower_name": data.get('bs', [{}])[0].get('n', 'New Case') if data.get('bs') else 'New Case',
            "bank": self.bank_var.get() if hasattr(self, 'bank_var') else 'None',
            "borrower_count": self.borr_var.get() if hasattr(self, 'borr_var') else '1',
            "loan_count": self.loan_var.get() if hasattr(self, 'loan_var') else '1',
            "last_updated": time.time(),
            "data": self.extracted_data,
            "verified_fields": list(self.verified_fields),
            "files": self.files,
            "watch_folder": self.watch_folder
        }
        path = os.path.join(self.cases_dir, self.active_case_id, "session.json")
        with open(path, "w") as f: json.dump(session, f)

        if show_feedback and hasattr(self, 'save_btn'):
            self.save_btn.config(text="SAVED ✓", state="normal")
            self.root.after(1500, lambda: self.save_btn.config(text="SAVE PROGRESS"))

    def _read_ui_to_dict(self):
        """Read the current state from the UI widgets into the extracted_data format."""
        if not hasattr(self, 'ents') or not self.ents:
            return None
        try:
            result = {}
            if 'rd' in self.ents:
                result['rd'] = self.get_val(self.ents['rd'])
            if 'ad' in self.ents:
                result['ad'] = self.get_val(self.ents['ad'])
            if self.ents.get('bs'):
                result['bs'] = [{k: self.get_val(v) for k, v in b.items()} for b in self.ents['bs']]
            if self.ents.get('ls'):
                result['ls'] = [{k: self.get_val(v) for k, v in l.items()} for l in self.ents['ls']]
            if self.ents.get('ps'):
                result['ps'] = [{k: self.get_val(v) for k, v in p.items()} for p in self.ents['ps']]
            if self.ents.get('ws'):
                result['ws'] = [{k: self.get_val(v) for k, v in w.items()} for w in self.ents['ws']]
            if 'bsign' in self.ents:
                result['bsign'] = {k: self.get_val(v) for k, v in self.ents['bsign'].items()}
            if 'ds_text' in self.ents:
                result['ds_text'] = self.get_val(self.ents['ds_text'])
            if 'second_schedule' in self.ents:
                result['second_schedule'] = self.get_val(self.ents['second_schedule'])
            return result
        except:
            return None

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
        if hasattr(self, 'bank_var'):
            saved_bank = session.get('bank', '')
            if saved_bank in self.bank_folders:
                self.bank_var.set(saved_bank)
                self.on_bank_change()
            saved_borr = session.get('borrower_count', '1')
            if saved_borr in self._available_borrower_counts():
                self.borr_var.set(saved_borr)
                self.on_borrower_change()
            saved_loan = session.get('loan_count', '1')
            if saved_loan in self._available_loan_counts():
                self.loan_var.set(saved_loan)
            self._update_template_display()
        self.display_data()

    def delete_case(self, case_id):
        if messagebox.askyesno("Delete Case", "Are you sure?"):
            shutil.rmtree(os.path.join(self.cases_dir, case_id))
            self.show_dashboard()

    # ===================== TEMPLATE DISCOVERY =====================

    def discover_templates(self):
        """Read subfolder names from templates/ as bank names.
        Inside each bank folder, scan .docx files matching: RM_{BANK}_{#B}B_{#L}L_*.docx
        template_map structure: {BANK: {B_COUNT: {L_COUNT: filepath}}}
        """
        self.template_map = {}
        self.bank_folders = []

        if not os.path.exists("templates"):
            return

        for item in os.listdir("templates"):
            bank_dir = os.path.join("templates", item)
            if not os.path.isdir(bank_dir):
                continue

            bank_name = item.upper()
            self.bank_folders.append(bank_name)
            self.template_map[bank_name] = {}

            for fname in os.listdir(bank_dir):
                if not fname.lower().endswith(".docx"):
                    continue
                # Parse: RM_{BANK}_{#B}B_{#L}L_anything.docx
                m = re.match(r"RM_" + re.escape(bank_name) + r"_(\d+)B_(\d+)L", fname, re.IGNORECASE)
                if m:
                    b_count = m.group(1)   # "1", "2", "3" etc.
                    l_count = m.group(2)   # "1", "2", "3" etc.
                    if b_count not in self.template_map[bank_name]:
                        self.template_map[bank_name][b_count] = {}
                    self.template_map[bank_name][b_count][l_count] = os.path.join(bank_dir, fname)

        self.bank_folders.sort()
        # Ensure ICICI is first if present
        if "ICICI" in self.bank_folders:
            self.bank_folders.remove("ICICI")
            self.bank_folders.insert(0, "ICICI")

    def _available_borrower_counts(self):
        """Return sorted list of borrower counts available for current bank."""
        bank = self.bank_var.get() if hasattr(self, 'bank_var') else ''
        bank_data = self.template_map.get(bank, {})
        return sorted(bank_data.keys(), key=int)

    def _available_loan_counts(self):
        """Return sorted list of loan counts available for current bank + borrower selection."""
        bank = self.bank_var.get() if hasattr(self, 'bank_var') else ''
        borr = self.borr_var.get() if hasattr(self, 'borr_var') else ''
        bank_data = self.template_map.get(bank, {})
        borr_data = bank_data.get(borr, {})
        return sorted(borr_data.keys(), key=int)

    def _get_auto_template_path(self):
        """Resolve the template path from current selections, or return None."""
        bank = self.bank_var.get() if hasattr(self, 'bank_var') else ''
        borr = self.borr_var.get() if hasattr(self, 'borr_var') else ''
        loan = self.loan_var.get() if hasattr(self, 'loan_var') else ''
        custom = self.custom_template_path.get().strip()
        if custom:
            return custom
        return self.template_map.get(bank, {}).get(borr, {}).get(loan)

    def _update_template_display(self):
        """Update the template label to show auto-selected file or custom path."""
        custom = self.custom_template_path.get().strip()
        if custom:
            self.template_lbl.config(text=f"Custom: {os.path.basename(custom)}", fg=ACCENT_BLUE_LIGHT)
            return
        path = self._get_auto_template_path()
        if path:
            self.template_lbl.config(text=f"Auto: {os.path.basename(path)}", fg=BTN_SUCCESS)
        else:
            self.template_lbl.config(text="No template available for this combination", fg=BTN_DANGER)

    # ===================== UI SETUP =====================

    def setup_ui(self):
        for w in self.root.winfo_children(): w.destroy()

        header = tk.Frame(self.root, bg=PRIMARY_NAV, height=70)
        header.pack(fill="x", side="top"); header.pack_propagate(False)
        tk.Label(header, text="LegalDoc Automator Pro", bg=PRIMARY_NAV, fg="white", font=("Segoe UI", 18, "bold"), padx=30).pack(side="left")
        tk.Button(header, text="BACK TO DASHBOARD", command=self.show_dashboard, bg=PRIMARY_NAV, fg="white", font=("Segoe UI", 8, "bold"), bd=0, padx=20, cursor="hand2").pack(side="left")

        # Save button with feedback
        self.save_btn = tk.Button(header, text="SAVE PROGRESS", command=lambda: self.save_case(show_feedback=True),
                                 bg=ACCENT_BLUE, fg="white", font=("Segoe UI", 8, "bold"),
                                 bd=0, padx=20, pady=10, cursor="hand2")
        self.save_btn.pack(side="left", padx=20)

        main_body = tk.Frame(self.root, bg=BG_MAIN); main_body.pack(fill="both", expand=True)

        self.left_p_container = tk.Frame(main_body, bg=SURFACE_CARD, width=400, bd=0, highlightthickness=1, highlightbackground=BORDER_COLOR)
        self.left_p_container.pack(side="left", fill="y", padx=(20, 10), pady=20); self.left_p_container.pack_propagate(False)

        canvas_l = tk.Canvas(self.left_p_container, bg=SURFACE_CARD, highlightthickness=0)
        scroll_l = ttk.Scrollbar(self.left_p_container, orient="vertical", command=canvas_l.yview)
        self.left_p = tk.Frame(canvas_l, bg=SURFACE_CARD, padx=20)
        self.left_p.bind("<Configure>", lambda e: canvas_l.configure(scrollregion=canvas_l.bbox("all")))
        canvas_l.create_window((0, 0), window=self.left_p, anchor="nw", width=360); canvas_l.configure(yscrollcommand=scroll_l.set); canvas_l.pack(side="left", fill="both", expand=True); scroll_l.pack(side="right", fill="y")
        # SINGLE GLOBAL MOUSEWHEEL HANDLER: routes to whichever panel the cursor is over
        def _global_mousewheel(event):
            x, y = self.root.winfo_pointerxy()
            widget = self.root.winfo_containing(x, y)
            if not widget:
                return
            w = widget
            while w and w != self.root:
                if w == canvas_r or w == self.scroll_f or w == self.right_p_container:
                    canvas_r.yview_scroll(int(-1*(event.delta/120)), "units")
                    return
                w = w.master
            # Default: scroll the left panel
            canvas_l.yview_scroll(int(-1*(event.delta/120)), "units")
        self.root.bind_all("<MouseWheel>", _global_mousewheel)

        # 1. CASE SETTINGS
        self.create_section_title(self.left_p, "1. CASE SETTINGS")
        cs_card = self.create_card(self.left_p)

        # -- Bank Selection --
        tk.Label(cs_card, text="Select Bank:", bg=SURFACE_CARD, font=FONT_HEADER, fg=TEXT_SECONDARY).pack(anchor="w")
        banks = self.bank_folders if self.bank_folders else ["ICICI"]
        self.bank_var = tk.StringVar(value=banks[0])
        self.bank_dropdown = ttk.Combobox(cs_card, textvariable=self.bank_var, values=banks, state="readonly")
        self.bank_dropdown.pack(fill="x", pady=(5, 15))
        self.bank_dropdown.bind("<<ComboboxSelected>>", lambda e: self.on_bank_change())

        # -- Borrower Count --
        tk.Label(cs_card, text="Borrower Count:", bg=SURFACE_CARD, font=FONT_HEADER, fg=TEXT_SECONDARY).pack(anchor="w")
        available_borr = self._available_borrower_counts()
        if not available_borr:
            available_borr = ["1"]
        self.borr_var = tk.StringVar(value=available_borr[0])
        self.borr_dropdown = ttk.Combobox(cs_card, textvariable=self.borr_var, values=available_borr, state="readonly")
        self.borr_dropdown.pack(fill="x", pady=(5, 10))
        self.borr_dropdown.bind("<<ComboboxSelected>>", lambda e: self.on_borrower_change())

        # -- Loan / Sanction Count --
        tk.Label(cs_card, text="Sanction/Loan Count:", bg=SURFACE_CARD, font=FONT_HEADER, fg=TEXT_SECONDARY).pack(anchor="w")
        available_loan = self._available_loan_counts()
        if not available_loan:
            available_loan = ["1"]
        self.loan_var = tk.StringVar(value=available_loan[0])
        self.loan_dropdown = ttk.Combobox(cs_card, textvariable=self.loan_var, values=available_loan, state="readonly")
        self.loan_dropdown.pack(fill="x", pady=(5, 10))
        self.loan_dropdown.bind("<<ComboboxSelected>>", lambda e: self._update_template_display())

        # 2. RM TEMPLATE
        self.create_section_title(self.left_p, "2. RM TEMPLATE")
        tm_card = self.create_card(self.left_p)
        tk.Button(tm_card, text="+ USE CUSTOM TEMPLATE DOCX", command=self.choose_template, bg="#EBF2FF", fg="#0D47A1", font=("Segoe UI", 9, "bold"), bd=0, pady=12, cursor="hand2").pack(fill="x")
        tk.Button(tm_card, text="Clear Custom Template", command=self.clear_template, bg=SURFACE_CARD, fg=BTN_DANGER, font=("Segoe UI", 7, "bold"), bd=0, pady=4, cursor="hand2").pack(pady=2)
        self.template_lbl = tk.Label(tm_card, text="Auto-selecting template", bg=SURFACE_CARD, fg=TEXT_SECONDARY, font=("Segoe UI", 8), wraplength=300)
        self.template_lbl.pack(pady=5)

        self._update_template_display()

        # 3. UPLOAD DOCUMENTS
        self.create_section_title(self.left_p, "3. UPLOAD DOCUMENTS")
        up_card = self.create_card(self.left_p)
        self.file_list = tk.Listbox(up_card, height=4, font=FONT_MONO, bd=0, highlightthickness=1, highlightbackground=BORDER_COLOR)
        self.file_list.pack(fill="x", pady=5)
        # Drag and drop support
        if DND_FILES:
            self.file_list.drop_target_register(DND_FILES)
            self.file_list.dnd_bind("<<Drop>>", self.drop_files)
        tk.Button(up_card, text="Browse Files", command=self.add_files, bg=SURFACE_CARD, fg=ACCENT_BLUE_LIGHT, font=("Segoe UI", 9, "bold"), bd=0, cursor="hand2").pack(pady=5)

        # 4. AI CONFIGURATION
        self.create_section_title(self.left_p, "4. AI CONFIGURATION")
        ai_card = self.create_card(self.left_p)
        tk.Label(ai_card, text="Gemini API Key:", bg=SURFACE_CARD, font=FONT_LABEL).pack(anchor="w")
        self.api_key_entry = tk.Entry(ai_card, show="*", font=FONT_MONO, bd=0, highlightthickness=1, highlightbackground=BORDER_COLOR)
        self.api_key_entry.insert(0, DEFAULT_GEMINI_API_KEY); self.api_key_entry.pack(fill="x", ipady=8, pady=5)

        # Model Selection
        tk.Label(ai_card, text="AI Model:", bg=SURFACE_CARD, font=FONT_LABEL).pack(anchor="w", pady=(8,0))
        model_values = self.available_models if self.available_models else ["gemini-1.5-flash"]
        self.model_dropdown = ttk.Combobox(ai_card, textvariable=self.model_var, values=model_values, state="readonly")
        self.model_dropdown.pack(fill="x", pady=5)
        tk.Button(ai_card, text="Refresh Models", command=self._refresh_models_click, bg="#EBF2FF", fg="#0D47A1", font=("Segoe UI", 8, "bold"), bd=0, pady=6, cursor="hand2").pack(fill="x", pady=(0,5))

        self.extract_btn = tk.Button(self.left_p, text="START AI AUTOMATION", command=self.start_process, bg=ACCENT_BLUE, fg="white", font=("Segoe UI", 12, "bold"), pady=15, bd=0, cursor="hand2")
        self.extract_btn.pack(fill="x", pady=30)

        self.status_var = tk.StringVar(value="Ready")
        tk.Label(self.left_p, textvariable=self.status_var, bg=SURFACE_CARD, fg=TEXT_SECONDARY, font=("Segoe UI", 9, "italic")).pack()

        # RIGHT PANEL: Verification & Editing
        self.right_p_container = tk.Frame(main_body, bg=BG_MAIN); self.right_p_container.pack(side="left", fill="both", expand=True, padx=(10, 20))
        canvas_r = tk.Canvas(self.right_p_container, bg=BG_MAIN, highlightthickness=0)
        scroll_r = ttk.Scrollbar(self.right_p_container, orient="vertical", command=canvas_r.yview)
        self.scroll_f = tk.Frame(canvas_r, bg=BG_MAIN, padx=20)
        self.scroll_f.bind("<Configure>", lambda e: canvas_r.configure(scrollregion=canvas_r.bbox("all")))
        canvas_r.create_window((0, 0), window=self.scroll_f, anchor="nw", width=900); canvas_r.configure(yscrollcommand=scroll_r.set); canvas_r.pack(side="left", fill="both", expand=True); scroll_r.pack(side="right", fill="y")

        # Mousewheel for right panel: capture events globally when mouse is over right_p_container
        def _r_mousewheel_bind(event):
            self.root.bind_all("<MouseWheel>", lambda e: canvas_r.yview_scroll(int(-1*(e.delta/120)), "units"), add="+")
            self.root.bind_all("<Button-4>", lambda e: canvas_r.yview_scroll(-3, "units"), add="+")
            self.root.bind_all("<Button-5>", lambda e: canvas_r.yview_scroll(3, "units"), add="+")
        def _r_mousewheel_unbind(event):
            self.root.unbind_all("<MouseWheel>")
            self.root.unbind_all("<Button-4>")
            self.root.unbind_all("<Button-5>")
            # Re-bind left panel mousewheel
            self._enable_mousewheel(canvas_l)
        canvas_r.bind("<Enter>", _r_mousewheel_bind)
        canvas_r.bind("<Leave>", _r_mousewheel_unbind)
        self.scroll_f.bind("<Enter>", _r_mousewheel_bind)
        self.scroll_f.bind("<Leave>", _r_mousewheel_unbind)

        self.ents = {"bs": [], "ls": [], "ps": [], "ws": [], "bsign": {}, "ds": None}
        self.display_data()

    # ===================== DROPDOWN CALLBACKS =====================

    def on_bank_change(self):
        """Called when the bank dropdown selection changes."""
        available_borr = self._available_borrower_counts()
        if available_borr:
            self.borr_var.set(available_borr[0])
            self.borr_dropdown['values'] = available_borr
        else:
            self.borr_var.set("1")
            self.borr_dropdown['values'] = ["1"]
        self.on_borrower_change()

    def on_borrower_change(self):
        """Called when the borrower count dropdown changes."""
        available_loan = self._available_loan_counts()
        if available_loan:
            self.loan_var.set(available_loan[0])
            self.loan_dropdown['values'] = available_loan
        else:
            self.loan_var.set("1")
            self.loan_dropdown['values'] = ["1"]
        self._update_template_display()

    # ===================== FILE / TEMPLATE HANDLING =====================

    def add_file_path(self, path):
        if not path or path in self.files or not os.path.isfile(path):
            return
        self.files.append(path)
        self.file_list.insert(tk.END, "  📄 " + os.path.basename(path))

    def drop_files(self, event):
        for path in self.root.tk.splitlist(event.data):
            self.add_file_path(path)

    def add_files(self):
        f_paths = filedialog.askopenfilenames(filetypes=[("Documents", "*.pdf *.jpg *.jpeg *.png")])
        for p in f_paths:
            if p not in self.files: self.files.append(p); self.file_list.insert(tk.END, "  📄 " + os.path.basename(p))

    def choose_template(self):
        p = filedialog.askopenfilename(filetypes=[("Word Document", "*.docx")])
        if p:
            self.custom_template_path.set(p)
            self._update_template_display()

    def clear_template(self):
        self.custom_template_path.set("")
        self._update_template_display()

    # ===================== AI AUTOMATION =====================

    def start_process(self):
        k, bank = self.api_key_entry.get().strip(), self.bank_var.get()
        if not k: messagebox.showerror("Error", "API Key required"); return
        if not self.files: messagebox.showerror("Error", "No files uploaded"); return
        self.extract_btn.config(state="disabled", text="PROCESSING...")
        model = self.model_var.get()
        threading.Thread(target=self.run_automation, args=(k, model, bank, self.borr_var.get(), self.loan_var.get()), daemon=True).start()

    def run_automation(self, k, m, bank, bc, lc):
        try:
            self.root.after(0, lambda: self.status_var.set("AI is processing..."))
            new_data = DataExtractor(k).extract_with_ai(self.files, m, bank_name=bank,
                                                       expected_borrowers=int(bc),
                                                       expected_loans=int(lc))
            self.extracted_data = self.smart_merge(self.extracted_data, new_data)
            self.root.after(0, self.display_data); self.root.after(0, lambda: self.save_case(show_feedback=True))
        except Exception as e: self.root.after(0, lambda msg=str(e): messagebox.showerror("Error", msg))
        finally:
            self.root.after(0, lambda: self.extract_btn.config(state="normal", text="START AI AUTOMATION"))
            self.root.after(0, lambda: self.status_var.set("Ready"))

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

    # ===================== DISPLAY / VERIFICATION UI =====================

    def display_data(self):
        for w in self.scroll_f.winfo_children(): w.destroy()
        if not self.extracted_data: return
        self.ents = {"bs": [], "ls": [], "ps": [], "ws": [], "bsign": {}, "ds": None}
        d = self.extracted_data

        tk.Label(self.scroll_f, text="VERIFICATION & EDITING", font=("Segoe UI", 18, "bold"), bg=BG_MAIN, fg=PRIMARY_NAV).pack(anchor="w", pady=(10, 20))

        dates_card = self.create_card(self.scroll_f, "EXECUTION DATES")
        self.ents["rd"] = self.create_input(dates_card, "RM Execution Date", d.get("rd", ""), field_path="rd")
        self.ents["ad"] = self.create_input(dates_card, "Loan Agreement Date", d.get("ad", ""), field_path="ad")

        self.create_section_title(self.scroll_f, "BORROWERS")
        for i, b in enumerate(d.get("bs", [])): self.add_borrower_ui(b, i)

        self.create_section_title(self.scroll_f, "LOAN ACCOUNTS")
        for i, l in enumerate(d.get("ls", [])): self.add_loan_ui(l, i)

        self.create_section_title(self.scroll_f, "PROPERTY SCHEDULES")
        for i, p in enumerate(d.get("ps", [])): self.add_property_ui(p, i)

        self.create_section_title(self.scroll_f, "BANK SIGNATORY")
        bsign_card = self.create_card(self.scroll_f)
        sig = d.get("bsign", {})
        self.ents["bsign"] = {
            "n": self.create_input(bsign_card, "Name", sig.get("n", ""), field_path="bsign.n"),
            "r": self.create_input(bsign_card, "Relation", sig.get("r", ""), field_path="bsign.r"),
            "rn": self.create_input(bsign_card, "Rel Name", sig.get("rn", ""), field_path="bsign.rn")
        }

        self.create_section_title(self.scroll_f, "WITNESSES")
        for i, w in enumerate(d.get("ws", [])): self.add_witness_ui(w, i)

        self.create_section_title(self.scroll_f, "DOCUMENT SCHEDULE / TITLE CHAIN (FIRST SCHEDULE)")
        ds_card = self.create_card(self.scroll_f)
        t = tk.Text(ds_card, height=10, bg="#F8FAFC", font=FONT_MONO, bd=0, highlightthickness=1, highlightbackground=BORDER_COLOR)
        t.pack(fill="x")
        raw_ds = d.get("ds_text", "") or d.get("ds", "")
        if isinstance(raw_ds, list):
            raw_ds = "\n".join([x.get("t","") if isinstance(x,dict) else str(x) for x in raw_ds])
        t.insert("1.0", str(raw_ds)); self.ents["ds_text"] = t

        self.create_section_title(self.scroll_f, "SECOND SCHEDULE (Annexure / Documents to be collected)")
        ss_card = self.create_card(self.scroll_f)
        ss = tk.Text(ss_card, height=8, bg="#F8FAFC", font=FONT_MONO, bd=0, highlightthickness=1, highlightbackground=BORDER_COLOR)
        ss.pack(fill="x")
        ss.insert("1.0", d.get("second_schedule", "")); self.ents["second_schedule"] = ss

        tk.Button(self.scroll_f, text="VERIFIED: GENERATE FINAL RM DOCX", command=self.generate,
                  bg=BTN_SUCCESS, fg="white", font=("Segoe UI", 13, "bold"), pady=20, bd=0, cursor="hand2").pack(fill="x", pady=40)

    def add_borrower_ui(self, b, i):
        f = self.create_card(self.scroll_f, f"BORROWER {i+1}")
        row = {
            "s": self.create_input(f, "Salutation", b.get("s",""), field_path=f"bs.{i}.s"),
            "n": self.create_input(f, "Name", b.get("n",""), field_path=f"bs.{i}.n"),
            "a": self.create_input(f, "Age", b.get("a",""), field_path=f"bs.{i}.a"),
            "r": self.create_input(f, "Relation", b.get("r",""), field_path=f"bs.{i}.r"),
            "rn": self.create_input(f, "Rel Name", b.get("rn",""), field_path=f"bs.{i}.rn"),
            "adr": self.create_input(f, "Address", b.get("adr",""), is_long=True, field_path=f"bs.{i}.adr"),
            "id": self.create_input(f, "Aadhar/ID", b.get("id",""), field_path=f"bs.{i}.id")
        }
        self.ents["bs"].append(row)

    def add_loan_ui(self, l, i):
        f = self.create_card(self.scroll_f, f"LOAN {i+1}")
        row = {
            "n": self.create_input(f, "LAN", l.get("n",""), field_path=f"ls.{i}.n"),
            "a": self.create_input(f, "Amount", l.get("a",""), field_path=f"ls.{i}.a"),
            "w": self.create_input(f, "Words", l.get("w",""), is_long=True, field_path=f"ls.{i}.w"),
            "t": self.create_input(f, "Tenure", l.get("t",""), field_path=f"ls.{i}.t")
        }
        self.ents["ls"].append(row)

    def add_property_ui(self, p, i):
        f = self.create_card(self.scroll_f, f"PROPERTY {i+1}")
        row = {
            "adr": self.create_input(f, "Address", p.get("adr",""), is_long=True, field_path=f"ps.{i}.adr"),
            "n": self.create_input(f, "North", p.get("n",""), field_path=f"ps.{i}.n"),
            "s": self.create_input(f, "South", p.get("s",""), field_path=f"ps.{i}.s"),
            "e": self.create_input(f, "East", p.get("e",""), field_path=f"ps.{i}.e"),
            "w": self.create_input(f, "West", p.get("w",""), field_path=f"ps.{i}.w")
        }
        self.ents["ps"].append(row)

    def add_witness_ui(self, w, i):
        f = self.create_card(self.scroll_f, f"WITNESS {i+1}")
        row = {
            "n": self.create_input(f, "Name", w.get("n",""), field_path=f"ws.{i}.n"),
            "r": self.create_input(f, "Relation", w.get("r",""), field_path=f"ws.{i}.r"),
            "rn": self.create_input(f, "Rel Name", w.get("rn",""), field_path=f"ws.{i}.rn"),
            "adr": self.create_input(f, "Address", w.get("adr",""), is_long=True, field_path=f"ws.{i}.adr")
        }
        self.ents["ws"].append(row)

    def get_val(self, w):
        return w.get("1.0", "end-1c").strip() if isinstance(w, tk.Text) else w.get().strip()

    def get_context_from_ui(self):
        try:
            # Get ds_text from the UI
            ds_text_val = self.get_val(self.ents['ds_text']) if 'ds_text' in self.ents else ''
            # Populate ds[] list from ds_text for backward compatibility with old templates
            ds_lines = [x.strip() for x in ds_text_val.split('\n') if x.strip()]
            ds_list = [{'t': line} for line in ds_lines] if ds_lines else [{'t': ds_text_val}]

            ctx = {
                'rd': self.get_val(self.ents['rd']) if 'rd' in self.ents else '',
                'ad': self.get_val(self.ents['ad']) if 'ad' in self.ents else '',
                'bs': [{k: self.get_val(v) for k, v in b.items()} for b in self.ents['bs']],
                'ls': [{k: self.get_val(v) for k, v in l.items()} for l in self.ents['ls']],
                'ps': [{k: self.get_val(v) for k, v in p.items()} for p in self.ents['ps']],
                'ws': [{k: self.get_val(v) for k, v in w.items()} for w in self.ents['ws']],
                'bsign': {k: self.get_val(v) for k, v in self.ents['bsign'].items()},
                'ds': ds_list,
                'ds_text': ds_text_val,
                'second_schedule': self.get_val(self.ents['second_schedule']) if 'second_schedule' in self.ents else ''
            }
            return ctx
        except Exception:
            # Return minimal valid context on error
            return {'rd': '', 'ad': '', 'bs': [{}], 'ls': [], 'ps': [], 'ws': [], 'bsign': {}, 'ds': [{'t':''}], 'ds_text': '', 'second_schedule': ''}

    # ===================== GENERATE FINAL RM =====================

    def generate(self):
        t_path = self._get_auto_template_path()
        if not t_path or not os.path.exists(t_path):
            messagebox.showerror("Error", "Template not found. Check bank/borrower/loan selection or set a custom template.")
            return

        bank = self.bank_var.get()
        sp = filedialog.asksaveasfilename(defaultextension=".docx", initialfile=f"RM_{bank}.docx")
        if sp:
            try:
                ctx = self.get_context_from_ui()
                # Save before generating so edits are captured
                self.save_case(show_feedback=False)
                TemplateProcessor(t_path).generate(ctx, sp, highlight_ai=True,
                                                  highlight_missing=True, verified_fields=self.verified_fields)
                messagebox.showinfo("Success", f"RM Generated successfully at:\n{sp}")
            except Exception as e:
                messagebox.showerror("Error", f"Generation failed: {str(e)}")


if __name__ == '__main__':
    root = TkinterDnD.Tk() if TkinterDnD else tk.Tk()
    LawApp(root)
    root.mainloop()