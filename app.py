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

PANEL_LEFT = SURFACE_CARD
TEXT_COLOR = TEXT_PRIMARY
DEFAULT_GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or "AIzaSyDs32YIJx35FDhb9qOa3vTcWDtU-RpL5_w"

class LawApp:
    def __init__(self, root):
        self.root = root
        self.root.title("LegalDoc Automator Pro v5")
        self.root.geometry("1400x980")
        self.root.configure(bg=BG_MAIN)
        self.active_case_id = None
        self.cases_dir = "cases"
        os.makedirs(self.cases_dir, exist_ok=True)
        self.files = []
        self.extracted_data = {}
        self.verified_fields = set()
        self.watch_folder = None
        self.template_map = {}
        self.custom_template_path = tk.StringVar(value="")
        self.discover_templates()
        self.show_dashboard()

    def create_section_title(self, parent, text):
        f = tk.Frame(parent, bg=parent["bg"])
        f.pack(fill="x", pady=(25, 12))
        tk.Label(f, text=text, bg=parent["bg"], fg=PRIMARY_NAV, font=FONT_DISPLAY, anchor="w").pack(side="left")
        tk.Frame(f, bg=BORDER_COLOR, height=1).pack(side="left", fill="x", expand=True, padx=(15, 0))

    def create_card(self, parent, title=None, is_danger=False):
        card = tk.Frame(parent, bg=SURFACE_CARD, bd=0, highlightthickness=1, highlightbackground=BTN_DANGER if is_danger else BORDER_COLOR)
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
        header.pack(fill="x", side="top"); header.pack_propagate(False)
        tk.Label(header, text="LegalDoc Automator Dashboard", bg=PRIMARY_NAV, fg="white", font=("Segoe UI", 18, "bold"), padx=30).pack(side="left")
        main_c = tk.Frame(self.root, bg=BG_MAIN, padx=40, pady=40); main_c.pack(fill="both", expand=True)
        actions = tk.Frame(main_c, bg=BG_MAIN); actions.pack(fill="x", pady=(0, 20))
        tk.Button(actions, text="+ NEW CASE SESSION", command=self.new_case, bg=ACCENT_BLUE, fg="white", font=("Segoe UI", 11, "bold"), padx=20, pady=12, bd=0, cursor="hand2").pack(side="left")
        self.create_section_title(main_c, "ACTIVE & PENDING CASES")
        scroll_c = tk.Frame(main_c, bg=BG_MAIN); scroll_c.pack(fill="both", expand=True)
        canvas = tk.Canvas(scroll_c, bg=BG_MAIN, highlightthickness=0)
        sb = ttk.Scrollbar(scroll_c, orient="vertical", command=canvas.yview)
        list_f = tk.Frame(canvas, bg=BG_MAIN); canvas.create_window((0,0), window=list_f, anchor="nw", width=1200)
        canvas.configure(yscrollcommand=sb.set); list_f.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.pack(side="left", fill="both", expand=True); sb.pack(side="right", fill="y")
        cases = self.list_cases()
        if not cases: tk.Label(list_f, text="No active cases found.", bg=BG_MAIN, fg=TEXT_SECONDARY, font=FONT_LABEL, pady=40).pack()
        else:
            for case in cases: self.add_dashboard_row(list_f, case)

    def add_dashboard_row(self, parent, case):
        c = self.create_card(parent); name = case.get('borrower_name', 'Unnamed Case') or 'Unnamed Case'
        bank = case.get('bank', 'Not Selected'); updated = time.strftime('%d %b, %H:%M', time.localtime(case.get('last_updated', 0)))
        left = tk.Frame(c, bg=SURFACE_CARD); left.pack(side="left", fill="x", expand=True)
        tk.Label(left, text=name, font=FONT_DISPLAY, bg=SURFACE_CARD, fg=TEXT_PRIMARY, anchor="w").pack(fill="x")
        tk.Label(left, text=f"{bank} | Updated: {updated}", font=FONT_LABEL, bg=SURFACE_CARD, fg=TEXT_SECONDARY, anchor="w").pack(fill="x")
        tk.Button(c, text="RESUME SESSION", command=lambda: self.load_case(case['id']), bg="#EBF2FF", fg=ACCENT_BLUE, font=("Segoe UI", 9, "bold"), padx=15, pady=8, bd=0, cursor="hand2").pack(side="right", padx=10)
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
        self.active_case_id = f"case_{int(time.time())}"; self.files, self.extracted_data, self.verified_fields, self.watch_folder = [], {}, set(), None
        os.makedirs(os.path.join(self.cases_dir, self.active_case_id), exist_ok=True); self.setup_ui()

    def save_case(self):
        if not self.active_case_id: return
        data = self.get_context_from_ui()
        session = {"id": self.active_case_id, "borrower_name": data['bs'][0].get('n', 'New Case') if data.get('bs') else 'New Case', "bank": self.bank_var.get() if hasattr(self, 'bank_var') else 'None', "last_updated": time.time(), "data": self.extracted_data, "verified_fields": list(self.verified_fields), "files": self.files, "watch_folder": self.watch_folder}
        path = os.path.join(self.cases_dir, self.active_case_id, "session.json")
        with open(path, "w") as f: json.dump(session, f)

    def load_case(self, case_id):
        path = os.path.join(self.cases_dir, case_id, "session.json")
        if not os.path.exists(path): return
        with open(path, "r") as f: session = json.load(f)
        self.active_case_id = session['id']; self.files = session.get('files', []); self.extracted_data = session.get('data', {}); self.verified_fields = set(session.get('verified_fields', [])); self.watch_folder = session.get('watch_folder')
        self.setup_ui(); self.bank_var.set(session.get('bank', 'ICICI')); self.display_data()

    def delete_case(self, case_id):
        if messagebox.askyesno("Delete Case", "Are you sure?"):
            shutil.rmtree(os.path.join(self.cases_dir, case_id)); self.show_dashboard()

    def setup_ui(self):
        for w in self.root.winfo_children(): w.destroy()
        header = tk.Frame(self.root, bg=PRIMARY_NAV, height=70); header.pack(fill="x", side="top"); header.pack_propagate(False)
        tk.Label(header, text="LegalDoc Automator Pro", bg=PRIMARY_NAV, fg="white", font=("Segoe UI", 18, "bold"), padx=30).pack(side="left")
        tk.Button(header, text="BACK TO DASHBOARD", command=self.show_dashboard, bg=PRIMARY_NAV, fg="white", font=("Segoe UI", 8, "bold"), bd=0, padx=20, cursor="hand2").pack(side="left")
        tk.Button(header, text="SAVE PROGRESS", command=self.save_case, bg=ACCENT_BLUE, fg="white", font=("Segoe UI", 8, "bold"), bd=0, padx=20, pady=10, cursor="hand2").pack(side="left", padx=20)
        main_body = tk.Frame(self.root, bg=BG_MAIN); main_body.pack(fill="both", expand=True)
        self.left_p_container = tk.Frame(main_body, bg=SURFACE_CARD, width=400, bd=0, highlightthickness=1, highlightbackground=BORDER_COLOR)
        self.left_p_container.pack(side="left", fill="y", padx=(20, 10), pady=20); self.left_p_container.pack_propagate(False)
        canvas_l = tk.Canvas(self.left_p_container, bg=SURFACE_CARD, highlightthickness=0)
        scroll_l = ttk.Scrollbar(self.left_p_container, orient="vertical", command=canvas_l.yview)
        self.left_p = tk.Frame(canvas_l, bg=SURFACE_CARD, padx=20)
        self.left_p.bind("<Configure>", lambda e: canvas_l.configure(scrollregion=canvas_l.bbox("all")))
        canvas_l.create_window((0, 0), window=self.left_p, anchor="nw", width=360); canvas_l.configure(yscrollcommand=scroll_l.set); canvas_l.pack(side="left", fill="both", expand=True); scroll_l.pack(side="right", fill="y")
        self.create_section_title(self.left_p, "1. CASE SETTINGS")
        cs_card = self.create_card(self.left_p); self.borr_var = tk.StringVar(value="Single"); self.loan_var = tk.StringVar(value="1 Loan")
        tk.Label(cs_card, text="Borrower Count:", bg=SURFACE_CARD, font=FONT_HEADER, fg=TEXT_SECONDARY).pack(anchor="w")
        tk.Radiobutton(cs_card, text="Single Borrower", variable=self.borr_var, value="Single", bg=SURFACE_CARD).pack(anchor="w")
        tk.Radiobutton(cs_card, text="Multiple Borrowers", variable=self.borr_var, value="Multiple", bg=SURFACE_CARD).pack(anchor="w", pady=(0, 10))
        tk.Label(cs_card, text="Loan Account Count:", bg=SURFACE_CARD, font=FONT_HEADER, fg=TEXT_SECONDARY).pack(anchor="w")
        tk.Radiobutton(cs_card, text="1 Loan Account", variable=self.loan_var, value="1 Loan", bg=SURFACE_CARD).pack(anchor="w")
        tk.Radiobutton(cs_card, text="2 Loan Accounts", variable=self.loan_var, value="2 Loans", bg=SURFACE_CARD).pack(anchor="w")
        tk.Label(self.left_p, text="Select Bank:", bg=SURFACE_CARD, font=FONT_HEADER, fg=TEXT_SECONDARY).pack(anchor="w", pady=(10,0))
        banks = sorted(list(self.template_map.keys())) if self.template_map else ["ICICI"]; self.bank_var = tk.StringVar(value=banks[0])
        ttk.Combobox(self.left_p, textvariable=self.bank_var, values=banks, state="readonly").pack(fill="x", pady=(5, 15))
        self.create_section_title(self.left_p, "2. RM TEMPLATE")
        tm_card = self.create_card(self.left_p); tk.Button(tm_card, text="+ USE CUSTOM TEMPLATE DOCX", command=self.choose_template, bg="#EBF2FF", fg=ACCENT_BLUE, font=("Segoe UI", 9, "bold"), bd=0, pady=12).pack(fill="x")
        self.create_section_title(self.left_p, "3. UPLOAD DOCUMENTS")
        up_card = self.create_card(self.left_p); self.file_list = tk.Listbox(up_card, height=4, font=FONT_MONO); self.file_list.pack(fill="x", pady=5)
        tk.Button(up_card, text="Browse Files", command=self.add_files, bg=SURFACE_CARD, fg=ACCENT_BLUE, font=("Segoe UI", 9, "bold"), bd=0).pack(pady=5)
        self.create_section_title(self.left_p, "4. AI CONFIGURATION")
        ai_card = self.create_card(self.left_p); self.api_key_entry = tk.Entry(ai_card, show="*", font=FONT_MONO); self.api_key_entry.insert(0, DEFAULT_GEMINI_API_KEY); self.api_key_entry.pack(fill="x", ipady=8)
        self.extract_btn = tk.Button(self.left_p, text="START AI AUTOMATION", command=self.start_process, bg=ACCENT_BLUE, fg="white", font=("Segoe UI", 12, "bold"), pady=15, bd=0); self.extract_btn.pack(fill="x", pady=30)
        self.right_p_container = tk.Frame(main_body, bg=BG_MAIN); self.right_p_container.pack(side="left", fill="both", expand=True, padx=(10, 20))
        canvas_r = tk.Canvas(self.right_p_container, bg=BG_MAIN, highlightthickness=0); scroll_r = ttk.Scrollbar(self.right_p_container, orient="vertical", command=canvas_r.yview)
        self.scroll_f = tk.Frame(canvas_r, bg=BG_MAIN, padx=20); self.scroll_f.bind("<Configure>", lambda e: canvas_r.configure(scrollregion=canvas_r.bbox("all")))
        canvas_r.create_window((0, 0), window=self.scroll_f, anchor="nw", width=900); canvas_r.configure(yscrollcommand=scroll_r.set); canvas_r.pack(side="left", fill="both", expand=True); scroll_r.pack(side="right", fill="y")
        self.ents = {"bs": [], "ls": [], "ps": [], "ws": []}; self.display_data()

    def discover_templates(self):
        self.template_map = {}
        if not os.path.exists("templates"): return
        for root_dir, _, names in os.walk("templates"):
            for name in names:
                if name.endswith(".docx"):
                    p = os.path.join(root_dir, name); m = re.search(r"RM_(.*?)_(\d)B_(\d)L\.docx", name)
                    if m:
                        b, bc, lc = m.group(1), m.group(2), m.group(3); bc_label = "Single" if bc=="1" else "Multiple"; lc_label = f"{lc} Loan" if lc=="1" else f"{lc} Loans"
                        if b not in self.template_map: self.template_map[b] = {"Single": {}, "Multiple": {}}
                        self.template_map[b][bc_label][lc_label] = p

    def add_files(self):
        f_paths = filedialog.askopenfilenames(filetypes=[("Documents", "*.pdf *.jpg *.jpeg *.png")])
        for p in f_paths:
            if p not in self.files: self.files.append(p); self.file_list.insert(tk.END, "  📄 " + os.path.basename(p))

    def choose_template(self):
        p = filedialog.askopenfilename(filetypes=[("Word Document", "*.docx")]); self.custom_template_path.set(p)

    def start_process(self):
        k, bank = self.api_key_entry.get().strip(), self.bank_var.get()
        if not k: messagebox.showerror("Error", "API Key required"); return
        if not self.files: messagebox.showerror("Error", "No files uploaded"); return
        self.extract_btn.config(state="disabled", text="PROCESSING..."); threading.Thread(target=self.run_automation, args=(k, "gemini-1.5-flash", bank, self.borr_var.get(), self.loan_var.get()), daemon=True).start()

    def run_automation(self, k, m, bank, bc, lc):
        try:
            new_data = DataExtractor(k).extract_with_ai(self.files, m, bank_name=bank, expected_borrowers=(1 if bc=="Single" else 2), expected_loans=(1 if lc=="1 Loan" else 2))
            self.extracted_data = self.smart_merge(self.extracted_data, new_data); self.root.after(0, self.display_data); self.root.after(0, self.save_case)
        except Exception as e: self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
        finally: self.root.after(0, lambda: self.extract_btn.config(state="normal", text="START AI AUTOMATION"))

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

    def display_data(self):
        for w in self.scroll_f.winfo_children(): w.destroy()
        if not self.extracted_data: return
        self.ents = {"bs": [], "ls": [], "ps": [], "ws": []}; d = self.extracted_data
        tk.Label(self.scroll_f, text="VERIFICATION & EDITING", font=("Segoe UI", 18, "bold"), bg=BG_MAIN, fg=PRIMARY_NAV).pack(anchor="w", pady=(10, 20))
        dates_card = self.create_card(self.scroll_f, "EXECUTION DATES")
        self.ents["rd"] = self.create_input(dates_card, "RM Execution Date", d.get("rd", ""), field_path="rd")
        self.create_section_title(self.scroll_f, "BORROWERS")
        for i, b in enumerate(d.get("bs", [])): self.add_borrower_ui(b, i)
        self.create_section_title(self.scroll_f, "LOAN ACCOUNTS")
        for i, l in enumerate(d.get("ls", [])): self.add_loan_ui(l, i)
        tk.Button(self.scroll_f, text="VERIFIED: GENERATE FINAL RM DOCX", command=self.generate, bg=BTN_SUCCESS, fg="white", font=("Segoe UI", 13, "bold"), pady=20, bd=0).pack(fill="x", pady=40)

    def create_input(self, parent, label, value, is_long=False, field_path=None):
        f = tk.Frame(parent, bg=SURFACE_CARD); f.pack(fill="x", pady=8)
        header_f = tk.Frame(f, bg=SURFACE_CARD); header_f.pack(fill="x")
        tk.Label(header_f, text=label.upper(), bg=SURFACE_CARD, fg=TEXT_SECONDARY, font=("Segoe UI", 8, "bold")).pack(side="left")
        is_verified = field_path in self.verified_fields if field_path else True
        bg_color = "#FEF9C3" if (value and not is_verified) else "#F8FAFC"
        if is_long:
            e = tk.Text(f, bg=bg_color, font=FONT_LABEL, height=3, bd=0, highlightthickness=1, highlightbackground=BORDER_COLOR, padx=10, pady=8); e.insert("1.0", str(value)); e.pack(fill="x", pady=(4, 0))
        else:
            e = tk.Entry(f, bg=bg_color, bd=0, font=FONT_LABEL, highlightthickness=1, highlightbackground=BORDER_COLOR); e.insert(0, str(value)); e.pack(fill="x", ipady=10, pady=(4, 0))
        if field_path:
            v_btn = tk.Button(header_f, text="✓ VERIFIED" if is_verified else "MARK VERIFIED", font=("Segoe UI", 7, "bold"), bg=SURFACE_CARD, fg=BTN_SUCCESS if is_verified else ACCENT_BLUE, bd=0)
            v_btn.pack(side="right")
            def toggle(p=field_path, b=v_btn, w=e):
                if p in self.verified_fields: self.verified_fields.remove(p); b.config(text="MARK VERIFIED", fg=ACCENT_BLUE); w.config(bg="#FEF9C3" if self.get_val(w) else "#F8FAFC")
                else: self.verified_fields.add(p); b.config(text="✓ VERIFIED", fg=BTN_SUCCESS); w.config(bg="#F8FAFC")
                self.save_case()
            v_btn.config(command=toggle)
        return e

    def add_borrower_ui(self, b, i):
        f = self.create_card(self.scroll_f, f"BORROWER {i+1}"); row = {"n": self.create_input(f, "Name", b.get("n",""), field_path=f"bs.{i}.n"), "adr": self.create_input(f, "Address", b.get("adr",""), is_long=True, field_path=f"bs.{i}.adr")}; self.ents["bs"].append(row)

    def add_loan_ui(self, l, i):
        f = self.create_card(self.scroll_f, f"LOAN {i+1}"); row = {"n": self.create_input(f, "LAN", l.get("n",""), field_path=f"ls.{i}.n"), "a": self.create_input(f, "Amount", l.get("a",""), field_path=f"ls.{i}.a")}; self.ents["ls"].append(row)

    def get_val(self, w): return w.get("1.0", "end-1c").strip() if isinstance(w, tk.Text) else w.get().strip()

    def get_context_from_ui(self):
        return {'rd': self.get_val(self.ents['rd']) if 'rd' in self.ents else '', 'bs': [{k: self.get_val(v) for k, v in b.items()} for b in self.ents['bs']], 'ls': [{k: self.get_val(v) for k, v in l.items()} for l in self.ents['ls']], 'ps': [], 'ws': [], 'bsign': {}, 'ds': []}

    def generate(self):
        bank, borr, loan = self.bank_var.get(), self.borr_var.get(), self.loan_var.get()
        t_path = self.custom_template_path.get() or (self.template_map.get(bank, {}).get(borr, {}).get(loan))
        if not t_path or not os.path.exists(t_path): messagebox.showerror("Error", "Template not found"); return
        sp = filedialog.asksaveasfilename(defaultextension=".docx", initialfile=f"RM_{bank}.docx")
        if sp:
            TemplateProcessor(t_path).generate(self.get_context_from_ui(), sp, highlight_ai=True, highlight_missing=True, verified_fields=self.verified_fields)
            messagebox.showinfo("Success", f"Generated: {sp}")

if __name__ == '__main__':
    root = TkinterDnD.Tk() if TkinterDnD else tk.Tk(); LawApp(root); root.mainloop()
