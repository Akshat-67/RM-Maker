import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import threading
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
        self.template_map = {
            "ICICI": {
                "Single": {
                    "1 Loan": "templates/ICICI_SINGLE_BORROWER_1_LOAN.docx",
                    "2 Loans": "templates/ICICI_SINGLE_BORROWER_2_LOANS.docx",
                    "3+ Loans": "templates/ICICI_SINGLE_BORROWER_3_LOANS.docx"
                },
                "Multiple": {
                    "1 Loan": "templates/ICICI_MULTI_BORROWER_2_LOANS.docx", # Use 2-loan template as fallback
                    "2 Loans": "templates/ICICI_MULTI_BORROWER_2_LOANS.docx",
                    "3+ Loans": "templates/ICICI_MULTI_BORROWER_2_LOANS.docx"
                }
            }
        }
        self.setup_ui()

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
        self.bank_var = tk.StringVar(value="ICICI")
        self.bank_dropdown = ttk.Combobox(left_p, textvariable=self.bank_var, values=["ICICI"], font=FONT_LABEL)
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

        # UI Rendering
        sec1 = tk.LabelFrame(self.scroll_f, text=" GENERAL INFO ", bg=PANEL_LEFT, font=FONT_HEADER, padx=15, pady=10); sec1.pack(fill="x", pady=10)
        self.ents['rd'] = self.create_input(sec1, "RM Date", d.get('rd',''))
        self.ents['ad'] = self.create_input(sec1, "Agreement Date", d.get('ad',''))

        self.ents['bs'] = []
        for i, b in enumerate(d.get('bs', [])):
            sec_b = tk.LabelFrame(self.scroll_f, text=f" BORROWER {i+1} ", bg=PANEL_LEFT, font=FONT_HEADER, padx=15, pady=10); sec_b.pack(fill="x", pady=10)
            self.ents['bs'].append({k: self.create_input(sec_b, k, b.get(k,'')) for k in ['s','n','a','r','rn','adr','id']})

        self.ents['ls'] = []
        for i, l in enumerate(d.get('ls', [])):
            sec_l = tk.LabelFrame(self.scroll_f, text=f" LOAN {i+1} ", bg=PANEL_LEFT, font=FONT_HEADER, padx=15, pady=10); sec_l.pack(fill="x", pady=10)
            self.ents['ls'].append({k: self.create_input(sec_l, k, l.get(k,'')) for k in ['n','a','w','t']})

        self.ents['ps'] = []
        for i, p in enumerate(d.get('ps', [])):
            sec_p = tk.LabelFrame(self.scroll_f, text=f" PROPERTY {i+1} ", bg=PANEL_LEFT, font=FONT_HEADER, padx=15, pady=10); sec_p.pack(fill="x", pady=10)
            self.ents['ps'].append({k: self.create_input(sec_p, k, p.get(k,'')) for k in ['adr','n','s','e','w']})

        self.ents['ws'] = []
        for i, w in enumerate(d.get('ws', [])):
            sec_w = tk.LabelFrame(self.scroll_f, text=f" WITNESS {i+1} ", bg=PANEL_LEFT, font=FONT_HEADER, padx=15, pady=10); sec_w.pack(fill="x", pady=10)
            self.ents['ws'].append({k: self.create_input(sec_w, k, w.get(k,'')) for k in ['n','r','rn','adr']})

        sec_end = tk.LabelFrame(self.scroll_f, text=" LEGAL ", bg=PANEL_LEFT, font=FONT_HEADER, padx=15, pady=10); sec_end.pack(fill="x", pady=10)
        bs = d.get('bsign', {}); self.ents['bsign'] = {k: self.create_input(sec_end, f"Bank {k}", bs.get(k,'')) for k in ['n','r','rn']}
        t = tk.Text(sec_end, height=8, bg="#F8F9FA", font=FONT_MONO, bd=0); t.pack(fill="x", pady=5)
        t.insert("1.0", "\n".join([x.get('t','') for x in d.get('ds', [])])); self.ents['ds'] = t

        tk.Button(self.scroll_f, text="VERIFIED: GENERATE FINAL MASTER WORD DOCX", command=self.generate, bg=ACCENT_BLUE, fg="white", font=("Segoe UI", 13, "bold"), pady=20, bd=0, cursor="hand2").pack(fill="x", pady=40)

    def create_input(self, parent, label, value):
        f = tk.Frame(parent, bg=PANEL_LEFT)
        f.pack(fill="x", pady=6)
        tk.Label(f, text=label, width=20, anchor="w", bg=PANEL_LEFT, font=FONT_LABEL, fg="#5F6368").pack(side="left")
        e = tk.Entry(f, bg="#F1F3F4", bd=0, font=FONT_LABEL, highlightthickness=1, highlightbackground=BORDER_COLOR)
        e.insert(0, str(value))
        e.pack(side="left", fill="x", expand=True, ipady=8)

        # Add focus effects
        e.bind("<FocusIn>", lambda event: e.config(highlightbackground=ACCENT_BLUE))
        e.bind("<FocusOut>", lambda event: e.config(highlightbackground=BORDER_COLOR))

        return e

    def generate(self):
        bank, borr, loan = self.bank_var.get(), self.borr_var.get(), self.loan_var.get()
        try: t_path = self.template_map[bank][borr][loan]
        except KeyError: messagebox.showerror("Error", "No template defined"); return

        c = {
            'rd': self.ents['rd'].get(), 'ad': self.ents['ad'].get(),
            'bs': [{k: v.get() for k, v in b.items()} for b in self.ents['bs']],
            'ls': [{k: v.get() for k, v in l.items()} for l in self.ents['ls']],
            'ps': [{k: v.get() for k, v in p.items()} for p in self.ents['ps']],
            'ws': [{k: v.get() for k, v in w.items()} for w in self.ents['ws']],
            'bsign': {k: v.get() for k, v in self.ents['bsign'].items()},
            'ds': [{'t': x.strip()} for x in self.ents['ds'].get("1.0", tk.END).split('\n') if x.strip()]
        }
        sp = filedialog.asksaveasfilename(defaultextension=".docx")
        if sp: TemplateProcessor(t_path).generate(c, sp); messagebox.showinfo("Success", "RM Generated!")

if __name__ == "__main__": root = tk.Tk(); LawApp(root); root.mainloop()
