import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import threading
from extractor import DataExtractor
from processor import TemplateProcessor

# --- DESIGN CONSTANTS ---
BG_MAIN = "#F5F7FA"     # Light grey background
PANEL_LEFT = "#FFFFFF"   # White left panel
ACCENT_BLUE = "#1A73E8"  # Modern Google Blue
BTN_GREEN = "#34A853"    # Success Green
TEXT_DARK = "#202124"   # Dark grey text
FONT_HEADER = ("Segoe UI", 12, "bold")
FONT_LABEL = ("Segoe UI", 10)
FONT_MONO = ("Consolas", 10)

class LawApp:
    def __init__(self, root):
        self.root = root
        self.root.title("LegalDoc Automator - Professional Edition")
        self.root.geometry("1300x900")
        self.root.configure(bg=BG_MAIN)

        self.files = []
        self.extracted_data = {}

        # Internal template logic
        self.template_map = {
            "ICICI": {
                "Single": {
                    "1 Loan": "templates/ICICI_SINGLE_BORROWER_1_LOAN.docx",
                    "2 Loans": "templates/ICICI_SINGLE_BORROWER_2_LOANS.docx",
                    "3+ Loans": "templates/ICICI_SINGLE_BORROWER_3_LOANS.docx"
                },
                "Multiple": {
                    "1 Loan": "templates/ICICI_MULTI_BORROWER_2_LOANS.docx",
                    "2 Loans": "templates/ICICI_MULTI_BORROWER_2_LOANS.docx",
                    "3+ Loans": "templates/ICICI_MULTI_BORROWER_2_LOANS.docx"
                }
            }
        }

        self.setup_styles()
        self.setup_ui()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TCombobox", padding=5)
        style.configure("TButton", font=FONT_LABEL)

    def setup_ui(self):
        # --- TOP HEADER ---
        header = tk.Frame(self.root, bg=ACCENT_BLUE, height=60)
        header.pack(fill="x")
        tk.Label(header, text="LegalDoc Automator Pro", fg="white", bg=ACCENT_BLUE,
                 font=("Segoe UI", 16, "bold"), padx=20, pady=15).pack(side="left")

        # --- MAIN CONTAINER ---
        main_container = tk.Frame(self.root, bg=BG_MAIN)
        main_container.pack(fill="both", expand=True, padx=20, pady=20)

        # --- LEFT PANEL: CONFIG ---
        left_p = tk.Frame(main_container, bg=PANEL_LEFT, width=450, padx=20, pady=20,
                          highlightbackground="#DADCE0", highlightthickness=1)
        left_p.pack(side="left", fill="y")
        left_p.pack_propagate(False)

        # 1. Bank Settings
        tk.Label(left_p, text="1. CASE SETTINGS", font=FONT_HEADER, bg=PANEL_LEFT, fg=ACCENT_BLUE).pack(anchor="w", pady=(0,15))

        self.create_lbl(left_p, "Select Financial Institution:")
        self.bank_var = tk.StringVar(value="ICICI")
        ttk.Combobox(left_p, textvariable=self.bank_var, values=["ICICI", "Home First", "Piramal"]).pack(fill="x", pady=5)

        self.create_lbl(left_p, "Number of Borrowers:")
        self.borr_var = tk.StringVar(value="Single")
        tk.Radiobutton(left_p, text="Individual / Single", variable=self.borr_var, value="Single", bg=PANEL_LEFT).pack(anchor="w")
        tk.Radiobutton(left_p, text="Joint / Multiple", variable=self.borr_var, value="Multiple", bg=PANEL_LEFT).pack(anchor="w")

        self.create_lbl(left_p, "Loan Facilities:")
        self.loan_var = tk.StringVar(value="1 Loan")
        tk.Radiobutton(left_p, text="Single Loan Account", variable=self.loan_var, value="1 Loan", bg=PANEL_LEFT).pack(anchor="w")
        tk.Radiobutton(left_p, text="Two Separate Accounts", variable=self.loan_var, value="2 Loans", bg=PANEL_LEFT).pack(anchor="w")
        tk.Radiobutton(left_p, text="Three or More Accounts", variable=self.loan_var, value="3+ Loans", bg=PANEL_LEFT).pack(anchor="w")

        # 2. File Upload
        tk.Label(left_p, text="\n2. DOCUMENT POOL", font=FONT_HEADER, bg=PANEL_LEFT, fg=ACCENT_BLUE).pack(anchor="w", pady=(10,5))
        tk.Button(left_p, text="+ UPLOAD KYC & SANCTION FILES", command=self.add_files,
                  bg=ACCENT_BLUE, fg="white", font=("Segoe UI", 10, "bold"), bd=0, pady=10).pack(fill="x", pady=5)

        self.file_list = tk.Listbox(left_p, height=12, bd=0, bg="#F8F9FA", font=("Segoe UI", 9))
        self.file_list.pack(fill="both", pady=5)
        tk.Button(left_p, text="Clear Selected Files", command=self.clear_files, bg="#F1F3F4", bd=0).pack(fill="x")

        # 3. AI Connection
        tk.Label(left_p, text="\n3. AI ENGINE", font=FONT_HEADER, bg=PANEL_LEFT, fg=ACCENT_BLUE).pack(anchor="w", pady=(10,5))
        self.api_key_entry = tk.Entry(left_p, show="*", bg="#F1F3F4", bd=0, font=FONT_MONO)
        self.api_key_entry.insert(0, "") # Placeholder
        self.api_key_entry.pack(fill="x", ipady=8, pady=5)

        btn_frame = tk.Frame(left_p, bg=PANEL_LEFT)
        btn_frame.pack(fill="x", pady=10)
        tk.Button(btn_frame, text="Test Health", command=self.test_connection, width=12).pack(side="left")
        self.extract_btn = tk.Button(btn_frame, text="START RM AUTOMATION", command=self.start_process,
                                     bg=BTN_GREEN, fg="white", font=("Segoe UI", 10, "bold"), bd=0, padx=20)
        self.extract_btn.pack(side="right", fill="x", expand=True, padx=(5,0))

        # --- RIGHT PANEL: VERIFICATION ---
        right_p = tk.Frame(main_container, bg=BG_MAIN, padx=20)
        right_p.pack(side="right", fill="both", expand=True)

        tk.Label(right_p, text="DATA VERIFICATION & CORRECTION", font=FONT_HEADER, bg=BG_MAIN, fg="#5F6368").pack(anchor="w", pady=(0,15))

        # Scrollable area for verification
        self.canvas = tk.Canvas(right_p, bg=BG_MAIN, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(right_p, orient="vertical", command=self.canvas.yview)
        self.scroll_f = tk.Frame(self.canvas, bg=BG_MAIN)
        self.scroll_f.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas_window = self.canvas.create_window((0,0), window=self.scroll_f, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.root.bind("<Configure>", self.resize_canvas)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

    def resize_canvas(self, event):
        self.canvas.itemconfig(self.canvas_window, width=self.canvas.winfo_width())

    def create_lbl(self, parent, text):
        tk.Label(parent, text=text, bg=PANEL_LEFT, font=("Segoe UI", 9), fg="#5F6368").pack(anchor="w", pady=(10, 0))

    def add_files(self):
        for p in filedialog.askopenfilenames():
            if p not in self.files: self.files.append(p); self.file_list.insert(tk.END, f"  📄 {os.path.basename(p)}")

    def clear_files(self):
        self.files = []; self.file_list.delete(0, tk.END)

    def test_connection(self):
        k = self.api_key_entry.get()
        if not k: messagebox.showwarning("Warning", "Enter API Key"); return
        try:
            extractor = DataExtractor(k)
            models = extractor.get_available_models()
            messagebox.showinfo("Health Report", f"✅ Connection OK\n✅ Models Accessible: {len(models)}\nPreferred: {extractor.get_available_models()[0] if models else 'None'}")
        except Exception as e:
            messagebox.showerror("Health Report", f"❌ Failed: {str(e)}")

    def start_process(self):
        k = self.api_key_entry.get()
        if not k or not self.files: messagebox.showerror("Incomplete", "Please upload files and provide API key."); return
        self.extract_btn.config(state="disabled", text="AI THINKING..."); self.root.update()
        threading.Thread(target=self.run_automation, args=(k,)).start()

    def run_automation(self, k):
        try:
            self.extracted_data = DataExtractor(k).extract_with_ai(self.files)
            self.root.after(0, self.display_data)
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("AI Error", str(e)))
        finally:
            self.root.after(0, lambda: self.extract_btn.config(state="normal", text="START RM AUTOMATION"))

    def display_data(self):
        for w in self.scroll_f.winfo_children(): w.destroy()
        if "error" in self.extracted_data:
            messagebox.showerror("AI Result", self.extracted_data["error"]); return

        self.ents = {}
        d = self.extracted_data

        # --- STYLISH SECTIONS ---
        # 1. Dates
        sec1 = tk.LabelFrame(self.scroll_f, text=" GENERAL INFO ", bg=PANEL_LEFT, font=FONT_HEADER, padx=15, pady=15)
        sec1.pack(fill="x", pady=10)
        self.ents['rd'] = self.create_input(sec1, "RM Execution Date", d.get('rd',''))
        self.ents['ad'] = self.create_input(sec1, "Loan Agreement Date", d.get('ad',''))

        # 2. Borrowers
        self.ents['bs'] = []
        for i, b in enumerate(d.get('bs', [])):
            sec_b = tk.LabelFrame(self.scroll_f, text=f" BORROWER {i+1} ", bg=PANEL_LEFT, font=FONT_HEADER, padx=15, pady=15)
            sec_b.pack(fill="x", pady=10)
            row = {
                's': self.create_input(sec_b, "Salutation", b.get('s','')),
                'n': self.create_input(sec_b, "Full Name", b.get('n','')),
                'a': self.create_input(sec_b, "Age", b.get('a','')),
                'r': self.create_input(sec_b, "Relation", b.get('r','')),
                'rn': self.create_input(sec_b, "Relative Name", b.get('rn','')),
                'adr': self.create_input(sec_b, "Full Address", b.get('adr',''))
            }
            self.ents['bs'].append(row)

        # 3. Loans
        self.ents['ls'] = []
        for i, l in enumerate(d.get('ls', [])):
            sec_l = tk.LabelFrame(self.scroll_f, text=f" LOAN ACCOUNT {i+1} ", bg=PANEL_LEFT, font=FONT_HEADER, padx=15, pady=15)
            sec_l.pack(fill="x", pady=10)
            row = {
                'n': self.create_input(sec_l, "LAN No.", l.get('n','')),
                'a': self.create_input(sec_l, "Amount (Fig)", l.get('a','')),
                'w': self.create_input(sec_l, "Amount (Words)", l.get('w','')),
                't': self.create_input(sec_l, "Tenure", l.get('t',''))
            }
            self.ents['ls'].append(row)

        # 4. Property
        self.ents['ps'] = []
        for i, p in enumerate(d.get('ps', [])):
            sec_p = tk.LabelFrame(self.scroll_f, text=f" PROPERTY DETAILS ", bg=PANEL_LEFT, font=FONT_HEADER, padx=15, pady=15)
            sec_p.pack(fill="x", pady=10)
            row = {
                'adr': self.create_input(sec_p, "Full Description", p.get('adr','')),
                'n': self.create_input(sec_p, "North Boundary", p.get('n','')),
                's': self.create_input(sec_p, "South Boundary", p.get('s','')),
                'e': self.create_input(sec_p, "East Boundary", p.get('e','')),
                'w': self.create_input(sec_p, "West Boundary", p.get('w',''))
            }
            self.ents['ps'].append(row)

        # 5. Bottom block
        sec_end = tk.LabelFrame(self.scroll_f, text=" SIGNATORIES & LEGAL ", bg=PANEL_LEFT, font=FONT_HEADER, padx=15, pady=15)
        sec_end.pack(fill="x", pady=10)

        bs = d.get('bsign', {})
        self.ents['bsign'] = {
            'n': self.create_input(sec_end, "Bank Rep Name", bs.get('n','')),
            'r': self.create_input(sec_end, "Relation", bs.get('r','')),
            'rn': self.create_input(sec_end, "Relative", bs.get('rn',''))
        }

        tk.Label(sec_end, text="Second Schedule (Paste LSR Docs):", bg=PANEL_LEFT).pack(anchor="w", pady=(10,5))
        t = tk.Text(sec_end, height=10, bg="#F8F9FA", font=FONT_MONO, bd=0); t.pack(fill="x")
        t.insert("1.0", "\n".join([x.get('t','') for x in d.get('ds', [])]))
        self.ents['ds'] = t

        tk.Button(self.scroll_f, text="VERIFIED: GENERATE FINAL REGISTERED MORTGAGE", command=self.generate,
                  bg=ACCENT_BLUE, fg="white", font=("Segoe UI", 12, "bold"), pady=15, bd=0).pack(fill="x", pady=30)

    def create_input(self, parent, label, value):
        f = tk.Frame(parent, bg=PANEL_LEFT); f.pack(fill="x", pady=5)
        tk.Label(f, text=label, width=20, anchor="w", bg=PANEL_LEFT, font=FONT_LABEL, fg="#5F6368").pack(side="left")
        e = tk.Entry(f, bg="#F1F3F4", font=FONT_LABEL, bd=0); e.insert(0, str(value)); e.pack(side="left", fill="x", expand=True, ipady=5)
        return e

    def generate(self):
        bank = self.bank_var.get()
        borr = self.borr_var.get()
        loan = self.loan_var.get()
        try:
            t_path = self.template_map[bank][borr][loan]
        except KeyError:
            messagebox.showerror("Error", f"Template not defined for {bank}/{borr}/{loan}"); return

        context = {
            'rd': self.ents['rd'].get(),
            'ad': self.ents['ad'].get(),
            'bs': [{k: v.get() for k, v in b.items()} for b in self.ents['bs']],
            'ls': [{k: v.get() for k, v in l.items()} for l in self.ents['ls']],
            'ps': [{k: v.get() for k, v in p.items()} for p in self.ents['ps']],
            'bsign': {k: v.get() for k, v in self.ents['bsign'].items()},
            'ds': [{'t': x.strip()} for x in self.ents['ds'].get("1.0", tk.END).split('\n') if x.strip()]
        }

        save_p = filedialog.asksaveasfilename(defaultextension=".docx")
        if save_p:
            TemplateProcessor(t_path).generate(context, save_p)
            messagebox.showinfo("Success", "RM Document Generated Successfully!")

if __name__ == "__main__":
    root = tk.Tk(); app = LawApp(root); root.mainloop()
