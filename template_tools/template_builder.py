import os
import sys
import json
import re
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from docx import Document
from docx.table import _Cell, Table
from docx.text.paragraph import Paragraph

# Add root directory to path so extractor can be found
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from extractor import DataExtractor

<<<<<<< HEAD
DEFAULT_API_KEYS = [
    os.getenv("GEMINI_API_KEY"),
    "AIzaSyBKkvXn_tTX2YVK_YzQPkm7FUDtYju43hc",
    "AIzaSyAXF1GYok40JQPkzg3rv2b_CGVJjDsaze8",
    "AQ.Ab8RN6LT45vwhXCygf42E1_cCExGjyFvD95qNo1vQ37hC3ZnBQ",
    "AIzaSyDs32YIJx35FDhb9qOa3vTcWDtU-RpL5_w"
]
DEFAULT_API_KEYS = list(dict.fromkeys([k for k in DEFAULT_API_KEYS if k]))
if not DEFAULT_API_KEYS:
    DEFAULT_API_KEYS = ["AIzaSyDs32YIJx35FDhb9qOa3vTcWDtU-RpL5_w"]

=======
>>>>>>> 3c8ef3700876862f09e11a95b6a2e9e767d3567e
class TemplateBuilder:
    def __init__(self, root):
        self.root = root
        self.root.title("LegalDoc Master Template Creator v5")
        self.root.geometry("1450x980")

        self.doc_path = ""
        self.mapping = {}
        self.checklist_items = []
        # Comprehensive schema for high-accuracy mapping
        self.expected_fields = [
            ("RM Execution Date", "{{rd}}"),
            ("Loan Agreement Date", "{{ad}}"),
<<<<<<< HEAD
            
            ("Borrower 1 - Salutation", "{{bs[0].s}}"),
            ("Borrower 1 - Name", "{{bs[0].n}}"),
            ("Borrower 1 - Age", "{{bs[0].a}}"),
            ("Borrower 1 - Relation", "{{bs[0].r}}"),
            ("Borrower 1 - Rel Name", "{{bs[0].rn}}"),
            ("Borrower 1 - Address", "{{bs[0].adr}}"),
            ("Borrower 1 - Aadhar/ID", "{{bs[0].id}}"),
            ("Borrower 1 - PAN Card", "{{bs[0].pan}}"),
            
            ("Borrower 2 - Salutation", "{{bs[1].s}}"),
            ("Borrower 2 - Name", "{{bs[1].n}}"),
            ("Borrower 2 - Age", "{{bs[1].a}}"),
            ("Borrower 2 - Relation", "{{bs[1].r}}"),
            ("Borrower 2 - Rel Name", "{{bs[1].rn}}"),
            ("Borrower 2 - Address", "{{bs[1].adr}}"),
            ("Borrower 2 - Aadhar/ID", "{{bs[1].id}}"),
            ("Borrower 2 - PAN Card", "{{bs[1].pan}}"),
            
            ("Borrower 3 - Salutation", "{{bs[2].s}}"),
            ("Borrower 3 - Name", "{{bs[2].n}}"),
            ("Borrower 3 - Age", "{{bs[2].a}}"),
            ("Borrower 3 - Relation", "{{bs[2].r}}"),
            ("Borrower 3 - Rel Name", "{{bs[2].rn}}"),
            ("Borrower 3 - Address", "{{bs[2].adr}}"),
            ("Borrower 3 - Aadhar/ID", "{{bs[2].id}}"),
            ("Borrower 3 - PAN Card", "{{bs[2].pan}}"),
            
            ("Loan 1 - LAN No", "{{ls[0].n}}"),
            ("Loan 1 - Amount (Figures)", "{{ls[0].a}}"),
            ("Loan 1 - Amount (Words)", "{{ls[0].w}}"),
            ("Loan 1 - Tenure", "{{ls[0].t}}"),
            
            ("Loan 2 - LAN No", "{{ls[1].n}}"),
            ("Loan 2 - Amount (Figures)", "{{ls[1].a}}"),
            ("Loan 2 - Amount (Words)", "{{ls[1].w}}"),
            ("Loan 2 - Tenure", "{{ls[1].t}}"),
            
            ("Loan 3 - LAN No", "{{ls[2].n}}"),
            ("Loan 3 - Amount (Figures)", "{{ls[2].a}}"),
            ("Loan 3 - Amount (Words)", "{{ls[2].w}}"),
            ("Loan 3 - Tenure", "{{ls[2].t}}"),
            
            ("Property 1 - Address", "{{ps[0].adr}}"),
            ("Property 1 - North", "{{ps[0].n}}"),
            ("Property 1 - South", "{{ps[0].s}}"),
            ("Property 1 - East", "{{ps[0].e}}"),
            ("Property 1 - West", "{{ps[0].w}}"),
            
            ("Property 2 - Address", "{{ps[1].adr}}"),
            ("Property 2 - North", "{{ps[1].n}}"),
            ("Property 2 - South", "{{ps[1].s}}"),
            ("Property 2 - East", "{{ps[1].e}}"),
            ("Property 2 - West", "{{ps[1].w}}"),
            
            ("Bank Signatory - Name", "{{bsign.n}}"),
            ("Bank Signatory - Age", "{{bsign.a}}"),
            ("Bank Signatory - Relation", "{{bsign.r}}"),
            ("Bank Signatory - Rel Name", "{{bsign.rn}}"),
            ("Bank Signatory - PAN Card", "{{bsign.pan}}"),
            ("Bank Signatory - Aadhar/ID", "{{bsign.id}}"),
            
            ("Witness 1 - Name", "{{ws[0].n}}"),
            ("Witness 1 - Relation", "{{ws[0].r}}"),
            ("Witness 1 - Rel Name", "{{ws[0].rn}}"),
            ("Witness 1 - Address", "{{ws[0].adr}}"),
            
            ("Witness 2 - Name", "{{ws[1].n}}"),
            ("Witness 2 - Relation", "{{ws[1].r}}"),
            ("Witness 2 - Rel Name", "{{ws[1].rn}}"),
            ("Witness 2 - Address", "{{ws[1].adr}}"),
            
            ("Document Schedule / Title Chain (FIRST SCHEDULE)", "{{ds_text}}"),
            ("Document Schedule 1 - Title Deed", "{{ds[0].t}}"),
            ("Document Schedule 2 - Title Deed", "{{ds[1].t}}"),
            ("Document Schedule 3 - Title Deed", "{{ds[2].t}}"),
            ("Document Schedule 4 - Title Deed", "{{ds[3].t}}"),
            ("Second Schedule (Documents to be collected)", "{{second_schedule}}"),
=======
            ("Borrower 1 Salutation", "{{bs[0].s}}"),
            ("Borrower 1 Name", "{{bs[0].n}}"),
            ("Borrower 1 Age", "{{bs[0].a}}"),
            ("Borrower 1 Relation (S/o, W/o)", "{{bs[0].r}}"),
            ("Borrower 1 Rel Name", "{{bs[0].rn}}"),
            ("Borrower 1 Address", "{{bs[0].adr}}"),
            ("Borrower 1 Aadhar/ID", "{{bs[0].id}}"),
            ("Borrower 2 Name", "{{bs[1].n}}"),
            ("Borrower 2 Relation", "{{bs[1].r}}"),
            ("Borrower 2 Rel Name", "{{bs[1].rn}}"),
            ("Borrower 2 Address", "{{bs[1].adr}}"),
            ("Borrower 2 Aadhar/ID", "{{bs[1].id}}"),
            ("Borrower 3 Name", "{{bs[2].n}}"),
            ("Loan 1 LAN No", "{{ls[0].n}}"),
            ("Loan 1 Amount (Value)", "{{ls[0].a}}"),
            ("Loan 1 Amount (Words)", "{{ls[0].w}}"),
            ("Loan 1 Tenure", "{{ls[0].t}}"),
            ("Property 1 Address", "{{ps[0].adr}}"),
            ("Property 1 North", "{{ps[0].n}}"),
            ("Property 1 South", "{{ps[0].s}}"),
            ("Property 1 East", "{{ps[0].e}}"),
            ("Property 1 West", "{{ps[0].w}}"),
            ("Bank Signatory Name", "{{bsign.n}}"),
            ("Bank Signatory Rel", "{{bsign.r}}"),
            ("Bank Signatory Rel Name", "{{bsign.rn}}"),
            ("Witness 1 Name", "{{ws[0].n}}"),
            ("Witness 1 Address", "{{ws[0].adr}}"),
            ("Witness 2 Name", "{{ws[1].n}}"),
            ("Witness 2 Address", "{{ws[1].adr}}")
>>>>>>> 3c8ef3700876862f09e11a95b6a2e9e767d3567e
        ]
        self.setup_ui()
<<<<<<< HEAD
        # Auto-fetch models in background
        threading.Thread(target=self._auto_fetch_models, daemon=True).start()

    def _auto_fetch_models(self):
        """Fetch available Gemini models on startup."""
        try:
            extractor = DataExtractor(api_keys=DEFAULT_API_KEYS)
            models = extractor.get_available_models()
            if models:
                self.available_models = models
                preferred = [m for m in models if "gemini-2.5-flash" in m.lower() or "gemini-2.0-flash" in m.lower()]
                best = preferred[0] if preferred else models[0]
                self.model_var.set(best)
                self.root.after(0, lambda: self._update_model_dropdown())
        except Exception:
            pass

    def _update_model_dropdown(self):
        if hasattr(self, 'model_dropdown') and self.model_dropdown:
            self.model_dropdown['values'] = self.available_models
            if self.model_var.get() not in self.available_models:
                self.model_var.set(self.available_models[0] if self.available_models else "gemini-1.5-flash")
=======
>>>>>>> 3c8ef3700876862f09e11a95b6a2e9e767d3567e

    def rotate_api_key_click(self):
        if not hasattr(self, 'current_key_idx'):
            self.current_key_idx = 0
        self.current_key_idx = (self.current_key_idx + 1) % len(DEFAULT_API_KEYS)
        new_key = DEFAULT_API_KEYS[self.current_key_idx]
        self.api_key_entry.delete(0, tk.END)
        self.api_key_entry.insert(0, new_key)
        # Fetch models with the new key in the background
        threading.Thread(target=self._refresh_models_with_key, args=(new_key,), daemon=True).start()
        messagebox.showinfo("API Key Switched", f"Switched to API Key #{self.current_key_idx + 1} (ends with ...{new_key[-4:]})")

    def _refresh_models_with_key(self, api_key):
        try:
            extractor = DataExtractor(api_key)
            models = extractor.get_available_models()
            if models:
                self.available_models = models
                preferred = [m for m in models if "gemini-2.5-flash" in m.lower() or "gemini-2.0-flash" in m.lower()]
                best = preferred[0] if preferred else models[0]
                self.model_var.set(best)
                self.root.after(0, lambda: self._update_model_dropdown())
        except Exception:
            pass

    def setup_ui(self):
        self.c_bg = "#F3F4F6"; self.c_panel = "#FFFFFF"; self.c_blue = "#1A73E8"; self.c_success = "#0F9D58"; self.c_danger = "#D93025"; self.c_border = "#DADCE0"; self.c_text = "#3C4043"
        self.root.configure(bg=self.c_bg)
        header = tk.Frame(self.root, bg=self.c_blue, height=70); header.pack(fill="x")
        tk.Label(header, text="MASTER TEMPLATE GENERATOR PRO", fg="white", bg=self.c_blue, font=("Segoe UI", 18, "bold"), padx=25).pack(side="left")
        main_content = tk.Frame(self.root, bg=self.c_bg); main_content.pack(fill="both", expand=True, padx=20, pady=15)
        left_panel = tk.Frame(main_content, bg=self.c_bg, width=520); left_panel.pack(side="left", fill="y", padx=(0, 15)); left_panel.pack_propagate(False)
        group1 = tk.LabelFrame(left_panel, text=" 1. SELECT SOURCE WORD DOCUMENT ", bg=self.c_panel, font=("Segoe UI", 10, "bold"), padx=15, pady=15, fg=self.c_blue); group1.pack(fill="x", pady=(0, 10))
        tk.Button(group1, text="OPEN .DOCX FILE", command=self.load_doc, bg=self.c_blue, fg="white", bd=0, pady=12, font=("Segoe UI", 10, "bold"), cursor="hand2").pack(fill="x")
        self.path_lbl = tk.Label(group1, text="No file selected", fg="#70757A", bg=self.c_panel, font=("Segoe UI", 9)); self.path_lbl.pack(pady=8)
        group2 = tk.LabelFrame(left_panel, text=" 2. AI CONFIGURATION ", bg=self.c_panel, font=("Segoe UI", 10, "bold"), padx=15, pady=15, fg=self.c_blue); group2.pack(fill="x", pady=10)
        tk.Label(group2, text="API Key:", bg=self.c_panel).pack(anchor="w")
        self.api_key_entry = tk.Entry(group2, show="*", bg="#F1F3F4", bd=0, font=("Consolas", 10)); self.api_key_entry.pack(fill="x", ipady=8, pady=5); self.api_key_entry.insert(0, os.getenv("GEMINI_API_KEY", ""))
        self.model_var = tk.StringVar(value="gemini-1.5-flash")
        self.model_dropdown = ttk.Combobox(group2, textvariable=self.model_var, values=["gemini-1.5-flash", "gemini-2.0-flash-exp"], font=("Segoe UI", 10)); self.model_dropdown.pack(fill="x", pady=5)
        tk.Button(group2, text="Verify Key & Get Models", command=self.refresh_models, bg="#E8F0FE", fg=self.c_blue, bd=0, font=("Segoe UI", 9, "bold")).pack(fill="x", pady=5)
        self.discover_btn = tk.Button(left_panel, text="🔍 START FULL AI DATA DISCOVERY", command=self.discover_data, bg=self.c_success, fg="white", font=("Segoe UI", 13, "bold"), bd=0, pady=18, cursor="hand2"); self.discover_btn.pack(fill="x", pady=15)
        group3 = tk.LabelFrame(left_panel, text=" 3. CURRENT MAPPING AUDIT ", bg=self.c_panel, font=("Segoe UI", 10, "bold"), padx=10, pady=10, fg=self.c_blue); group3.pack(fill="both", expand=True, pady=10)
        self.tree = ttk.Treeview(group3, columns=("Raw", "Tag"), show='headings'); self.tree.heading("Raw", text="Exact Document Substring"); self.tree.heading("Tag", text="Placeholder Tag (Jinja2)"); self.tree.column("Raw", width=320); self.tree.column("Tag", width=160); self.tree.pack(side="left", fill="both", expand=True)
        sb = ttk.Scrollbar(group3, orient="vertical", command=self.tree.yview); self.tree.configure(yscrollcommand=sb.set); sb.pack(side="right", fill="y")
        mid_panel = tk.Frame(main_content, bg=self.c_panel, width=450, highlightbackground=self.c_border, highlightthickness=1); mid_panel.pack(side="left", fill="y", padx=15); mid_panel.pack_propagate(False)
        tk.Label(mid_panel, text="VERIFICATION CHECKLIST", font=("Segoe UI", 14, "bold"), bg=self.c_panel, pady=20, fg=self.c_text).pack()
        check_container = tk.Frame(mid_panel, bg=self.c_panel); check_container.pack(fill="both", expand=True, padx=20)
        check_canvas = tk.Canvas(check_container, bg=self.c_panel, highlightthickness=0); check_sb = ttk.Scrollbar(check_container, orient="vertical", command=check_canvas.yview); self.check_scroll_f = tk.Frame(check_canvas, bg=self.c_panel)
        self.check_scroll_f.bind("<Configure>", lambda e: check_canvas.configure(scrollregion=check_canvas.bbox("all"))); check_canvas.create_window((0,0), window=self.check_scroll_f, anchor="nw"); check_canvas.configure(yscrollcommand=check_sb.set); check_canvas.pack(side="left", fill="both", expand=True); check_sb.pack(side="right", fill="y"); self.init_checklist()
        right_panel = tk.Frame(main_content, bg=self.c_bg, width=380); right_panel.pack(side="left", fill="y", padx=(10, 0)); right_panel.pack_propagate(False)
        r1 = tk.LabelFrame(right_panel, text=" SMART GAP FIXER ", bg=self.c_panel, font=("Segoe UI", 10, "bold"), padx=15, pady=15, fg=self.c_danger); r1.pack(fill="x", pady=(0, 10))
        self.refetch_btn = tk.Button(r1, text="REFETCH UNCHECKED FIELDS", command=self.refetch_missing, bg=self.c_danger, fg="white", font=("Segoe UI", 10, "bold"), bd=0, pady=15, cursor="hand2"); self.refetch_btn.pack(fill="x")
        r2 = tk.LabelFrame(right_panel, text=" MANUAL CORRECTION ", bg=self.c_panel, font=("Segoe UI", 10, "bold"), padx=15, pady=15, fg="#5F6368"); r2.pack(fill="x", pady=15)
        self.manual_key = tk.Entry(r2, bg="#F1F3F4", bd=0, font=("Segoe UI", 10)); self.manual_key.pack(fill="x", ipady=10); self.manual_key.insert(0, "Exact text from doc")
        self.manual_tag = tk.Entry(r2, bg="#F1F3F4", bd=0, font=("Segoe UI", 10)); self.manual_tag.pack(fill="x", ipady=10, pady=10); self.manual_tag.insert(0, "{{tag}}")
        tk.Button(r2, text="ADD TO MAPPING", command=self.add_manual, bg="#5F6368", fg="white", bd=0, pady=10, font=("Segoe UI", 9, "bold")).pack(fill="x")
        tk.Button(r2, text="REMOVE SELECTED", command=self.delete_selected, fg=self.c_danger, bg=self.c_panel, bd=1, pady=5).pack(fill="x", pady=10)
        self.save_btn = tk.Button(right_panel, text="GENERATE FINAL\nMASTER TEMPLATE", command=self.generate_master, bg=self.c_blue, fg="white", font=("Segoe UI", 14, "bold"), bd=0, pady=30, cursor="hand2"); self.save_btn.pack(fill="x", side="bottom", pady=20)

    def init_checklist(self):
        for w in self.check_scroll_f.winfo_children(): w.destroy()
        self.checklist_items = []
        for label, tag in self.expected_fields:
            f = tk.Frame(self.check_scroll_f, bg=self.c_panel); f.pack(fill="x", pady=4)
            var = tk.BooleanVar(value=False); cb = tk.Checkbutton(f, text=f"{label}  ({tag})", variable=var, bg=self.c_panel, font=("Segoe UI", 10)); cb.pack(side="left"); self.checklist_items.append((label, tag, var, cb))

<<<<<<< HEAD
        tk.Label(group2, text="API Key:", bg=self.c_panel, font=("Segoe UI", 9)).pack(anchor="w")
        self.api_key_entry = tk.Entry(group2, show="*", bg="#F1F3F4", bd=0, font=("Consolas", 10))
        self.api_key_entry.insert(0, DEFAULT_API_KEYS[0])
        self.api_key_entry.pack(fill="x", ipady=8, pady=5)

        rotate_btn = tk.Button(group2, text="🔄 Rotate / Switch API Key", command=self.rotate_api_key_click, bg="#E8F0FE", fg=self.c_blue, bd=0, font=("Segoe UI", 8, "bold"), cursor="hand2")
        rotate_btn.pack(fill="x", pady=2)

        tk.Label(group2, text="AI Model:", bg=self.c_panel, font=("Segoe UI", 9)).pack(anchor="w", pady=(5,0))
        model_values = self.available_models if self.available_models else ["gemini-1.5-flash"]
        self.model_dropdown = ttk.Combobox(group2, textvariable=self.model_var, values=model_values, state="readonly", font=("Segoe UI", 10))
        self.model_dropdown.pack(fill="x", pady=5)
        tk.Button(group2, text="Refresh Models", command=self._refresh_models_click, bg="#E8F0FE", fg=self.c_blue, bd=0, font=("Segoe UI", 8, "bold")).pack(fill="x", pady=5)

        # Discovery Button
        self.discover_btn = tk.Button(left_panel, text="🔍 START AI DISCOVERY", command=self.discover_data, bg=self.c_success, fg="white", font=("Segoe UI", 13, "bold"), bd=0, pady=18, cursor="hand2")
        self.discover_btn.pack(fill="x", pady=10)

        # Mapping Tree (shows ONLY what was found)
        group3 = tk.LabelFrame(left_panel, text=" 3. DISCOVERED MAPPINGS ", bg=self.c_panel, font=("Segoe UI", 10, "bold"), padx=10, pady=10, fg=self.c_blue)
        group3.pack(fill="both", expand=True, pady=10)

        self.tree = ttk.Treeview(group3, columns=("Raw", "Tag"), show='headings', height=12)
        self.tree.heading("Raw", text="Exact Document Text")
        self.tree.heading("Tag", text="Placeholder Tag")
        self.tree.column("Raw", width=280)
        self.tree.column("Tag", width=160)
        self.tree.pack(side="left", fill="both", expand=True)

        sb = ttk.Scrollbar(group3, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set); sb.pack(side="right", fill="y")

        self.mapping_count_label = tk.Label(left_panel, text="", bg=self.c_bg, fg=self.c_text, font=("Segoe UI", 9, "italic"))
        self.mapping_count_label.pack(fill="x")

        # ============ RIGHT PANEL: Smart Manual Mapping ============
        right_panel = tk.Frame(main_content, bg=self.c_bg, width=600)
        right_panel.pack(side="left", fill="both", expand=True, padx=(10, 0))

        # Top section: Smart Manual Mapping with dropdown
        r1 = tk.LabelFrame(right_panel, text=" SMART MANUAL MAPPING ", bg=self.c_panel, font=("Segoe UI", 10, "bold"), padx=15, pady=15, fg=self.c_text)
        r1.pack(fill="x", pady=(0, 10))

        tk.Label(r1, text="Step 1: Type the EXACT text from the document:", bg=self.c_panel, font=("Segoe UI", 9), anchor="w").pack(fill="x")
        self.manual_text_entry = tk.Entry(r1, bg="#F1F3F4", bd=0, font=("Segoe UI", 10), highlightthickness=1, highlightbackground=self.c_border)
        self.manual_text_entry.pack(fill="x", ipady=10, pady=5)
        self.manual_text_entry.insert(0, "")

        tk.Label(r1, text="Step 2: Choose the placeholder tag from the dropdown:", bg=self.c_panel, font=("Segoe UI", 9), anchor="w").pack(fill="x")
        self.manual_tag_display = tk.StringVar()
        tag_display_values = [f"{label}  →  {tag}" for label, tag in self.all_tags]
        self.manual_tag_dropdown = ttk.Combobox(r1, textvariable=self.manual_tag_display, values=tag_display_values, state="normal", font=("Segoe UI", 10))
        self.manual_tag_dropdown.pack(fill="x", ipady=4, pady=5)

        btn_frame = tk.Frame(r1, bg=self.c_panel)
        btn_frame.pack(fill="x", pady=5)
        tk.Button(btn_frame, text="+ ADD MAPPING", command=self.add_manual, bg=self.c_blue, fg="white", bd=0, pady=10, font=("Segoe UI", 9, "bold"), cursor="hand2").pack(side="left", padx=(0, 10))
        tk.Button(btn_frame, text="REMOVE SELECTED", command=self.delete_selected, fg=self.c_danger, bg=self.c_panel, bd=1, pady=10, cursor="hand2").pack(side="left")
        tk.Button(btn_frame, text="CLEAR ALL", command=self.clear_all, fg=self.c_danger, bg=self.c_panel, bd=1, pady=10, cursor="hand2").pack(side="left", padx=10)

        # Scrollable verification list (takes all remaining space between mapping and generate)
        ver_label = tk.Label(right_panel, text="DISCOVERED MAPPINGS:", bg=self.c_bg, fg=self.c_text, font=("Segoe UI", 9, "bold"), anchor="w")
        ver_label.pack(fill="x", pady=(10, 2))

        ver_frame_wrapper = tk.Frame(right_panel, bg=self.c_panel, highlightthickness=1, highlightbackground=self.c_border)
        ver_frame_wrapper.pack(fill="both", expand=True)

        ver_canvas = tk.Canvas(ver_frame_wrapper, bg=self.c_panel, highlightthickness=0)
        ver_sb = ttk.Scrollbar(ver_frame_wrapper, orient="vertical", command=ver_canvas.yview)
        self.ver_frame = tk.Frame(ver_canvas, bg=self.c_panel)
        self.ver_frame.bind("<Configure>", lambda e: ver_canvas.configure(scrollregion=ver_canvas.bbox("all")))
        ver_canvas.create_window((0, 0), window=self.ver_frame, anchor="nw", width=560)
        ver_canvas.configure(yscrollcommand=ver_sb.set)
        ver_canvas.pack(side="left", fill="both", expand=True)
        ver_sb.pack(side="right", fill="y")

        # MASSIVE GENERATE BUTTON -- ALWAYS VISIBLE AT BOTTOM
        self.save_btn = tk.Button(right_panel, text=">>  GENERATE FINAL MASTER TEMPLATE  >>",
                                  command=self.generate_master,
                                  bg="#1A73E8", fg="white",
                                  font=("Segoe UI", 14, "bold"),
                                  bd=0, pady=25, cursor="hand2",
                                  activebackground="#1557B0", activeforeground="white")
        self.save_btn.pack(fill="x", pady=(15, 5))

    def _refresh_models_click(self):
        self._update_model_dropdown()
        messagebox.showinfo("Models", f"Using: {self.model_var.get()}")

    # ===================== FILE / LOAD =====================
=======
    def update_checklist_status(self):
        all_mapped_tags = " ".join(self.mapping.values())
        for label, tag, var, cb in self.checklist_items:
            found = tag in all_mapped_tags; var.set(found); cb.config(fg=self.c_success if found else self.c_danger)
>>>>>>> 3c8ef3700876862f09e11a95b6a2e9e767d3567e

    def load_doc(self):
        p = filedialog.askopenfilename(filetypes=[("Word Document", "*.docx")])
        if p: self.doc_path = p; self.path_lbl.config(text=os.path.basename(p), fg=self.c_blue)

    def refresh_models(self):
        k = self.api_key_entry.get().strip()
        if not k: messagebox.showwarning("Key Required", "Provide Gemini API Key."); return
        try:
            models = DataExtractor(k).get_available_models()
            if models: self.model_dropdown['values'] = models; self.model_var.set(models[0]); messagebox.showinfo("AI System", f"Found {len(models)} models.")
        except Exception as e: messagebox.showerror("AI Error", str(e))

    def discover_data(self):
        if not self.doc_path or not self.api_key_entry.get(): messagebox.showwarning("Missing Info", "Select doc and provide API key."); return
        self.discover_btn.config(state="disabled", text="AI SCANNING..."); threading.Thread(target=self.run_ai_discovery).start()

    def run_ai_discovery(self):
        try:
<<<<<<< HEAD
            doc = Document(self.doc_path)
            content = self.get_doc_content(doc)

            prompt = f"""
            CRITICAL MISSION: CONVERT COMPLETED DOCUMENT TO MASTER JINJA2 TEMPLATE.
            You are an expert legal document analyst. Your goal is 100% discovery of variable data.
            Identify ALL case-specific variable fields in the text below and map them to our system.

            CORE TAG SCHEMA:
            - rd: RM Execution Date (e.g., '10th day of May 2024')
            - ad: Loan Agreement Date (e.g., '15.04.2024')
            - bs[i]: Borrowers list. s=Salutation, n=Name, a=Age, r=Relation, rn=Rel Name, adr=Address, id=Aadhar/ID, pan=PAN Card
            - ls[i]: Loans list. n=LAN No, a=Amount in Figures, w=Amount in Words, t=Tenure
            - ps[i]: Property schedules. adr=Address, n=North, s=South, e=East, w=West
            - bsign: Bank Signatory. n=Name, a=Age, r=Relation, rn=Relative Name, id=Aadhar/ID, pan=PAN Card
            - ws[i]: Witnesses list. n=Name, r=Relation, rn=Relative Name, adr=Address
            - ds[i]: Document Schedule. t=Title deed description text

            MAPPING RULES:
            1. MINIMAL VALUE MAPPING (MANDATORY): Return the smallest exact variable text, not the static legal wording around it.
               GOOD: {{"24th day of March 2024": "{{{{rd}}}}"}}
               GOOD: {{"17,15,000": "{{{{ls[0].a}}}}"}}
               GOOD: {{"180 Months": "{{{{ls[0].t}}}}"}}
               BAD: {{"this 24th day of March 2024": "this {{{{rd}}}}"}}
               BAD: {{"MORTGAGE MONEY RS. 17,15,000/-": "MORTGAGE MONEY RS. {{{{ls[0].a}}}}/-"}}

            2. EXACT MATCH: The JSON key must be copied EXACTLY as it appears in the document text.
            3. ENTITY INDEXING: Use [0] for the first entity, [1] for the second, etc.
            4. EXHAUSTIVE SEARCH: Look into headers, footers, and table cells.
            5. DO NOT MISS THESE COMMONLY MISSED FIELDS:
               - salutations: Mr., Mrs., Ms., Shri, Smt.
               - relations: S/o, W/o, D/o, Son of, Wife of, Daughter of
               - relative names following those relation markers
               - both witness names, relations, relative names, and full addresses
               - bank signatory age: MUST extract this if present (e.g., 'Age 26 years', 'Age 26', '26 Years', 'aged 26 years' next to the signatory's details).
               - full property address/schedule and all boundaries
               - loan tenure such as 120 Months, 180 Months, 240 Months
               - Aadhaar / UID numbers: Any 12-digit identification numbers next to borrower, mortgagor, or bank signatory details, whether formatted with hyphens (e.g. '5130-5171-6826', '7837-7620-4939'), spaces (e.g. '3793 2529 5076'), or raw digits (e.g. '379325295076'). You MUST map them exactly to the corresponding bs[i].id or bsign.id.
               - PAN Card numbers: Any 10-character alphanumeric PAN strings (e.g. 'AAECM6252D', 'IHYPD3537A') next to borrower, mortgagor, or bank signatory details. You MUST map them exactly to the corresponding bs[i].pan or bsign.pan.
            6. If a line reads like "Mr. Ram Kumar S/o Shyam Lal R/o Jaipur", map it separately:
               {{"Mr. Ram Kumar": "{{{{bs[0].s}}}} {{{{bs[0].n}}}}", "S/o Shyam Lal": "{{{{bs[0].r}}}} {{{{bs[0].rn}}}}"}}
            7. BANK SIGNATORY DETAILED MAPPING:
               If a signatory line reads like "through its authorized person Mr. Nitin Jangid S/o Suresh Jangid, Age 26 years", map it separately:
               {{"Mr. Nitin Jangid": "{{{{bsign.n}}}}", "S/o Suresh Jangid": "{{{{bsign.r}}}} {{{{bsign.rn}}}}", "Age 26 years": "Age {{{{bsign.a}}}} years"}}
            8. DANGEROUS NAKED NUMBERS (CRITICAL): Never map a single naked number for Age (e.g., {{"26": "{{{{bsign.a}}}}"}}). Always include the surrounding context like "Age" and "years" to prevent corrupting dates or other numbers (e.g., {{"Age 26 years": "Age {{{{bsign.a}}}} years"}} or {{"Age 26": "Age {{{{bsign.a}}}}"}}). This applies to borrower/witness ages as well.

            Return ONLY a valid JSON dictionary. No preamble.

            DOCUMENT TEXT:
            {content}
            """

            entered_key = self.api_key_entry.get().strip()
            # Combine entered key with defaults to ensure failover works
            keys = [entered_key] + [k for k in DEFAULT_API_KEYS if k != entered_key]
            extractor = DataExtractor(api_keys=keys)
=======
            doc = Document(self.doc_path); content = self.get_doc_content(doc)
            prompt = f"Identify variable fields and map to tags: rd, ad, bs[i].(s,n,a,r,rn,adr,id), ls[i].(n,a,w,t), ps[i].(adr,n,s,e,w), bsign.(n,r,rn), ws[i].(n,r,rn,adr). Return ONLY JSON dictionary {{'Exact Doc Text': '{{{{tag}}}}'}}. Text:\n{content}"
            extractor = DataExtractor(self.api_key_entry.get())
>>>>>>> 3c8ef3700876862f09e11a95b6a2e9e767d3567e
            raw = extractor.raw_generate(prompt, self.model_var.get())
            match = re.search(r'\{.*\}', raw or "", re.DOTALL)
            if match:
                self.mapping = self.clean_mapping(json.loads(match.group(0)))
                self.mapping.update(self.suggest_common_mappings(content, self.mapping))
                self.root.after(0, self.update_tree)
        except Exception as e: self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
        finally: self.root.after(0, lambda: self.discover_btn.config(state="normal", text="🔍 START FULL AI DATA DISCOVERY"))

    def refetch_missing(self):
        missing = [tag for label, tag, var, cb in self.checklist_items if not var.get()]
        if not missing: return
        self.refetch_btn.config(state="disabled", text="FIXING GAPS..."); threading.Thread(target=self.run_gap_fix, args=(missing,)).start()

    def run_gap_fix(self, missing_tags):
        try:
            doc = Document(self.doc_path); content = self.get_doc_content(doc)
            prompt = f"Find exact doc strings for missing tags: {missing_tags}. Return ONLY JSON. Text:\n{content}"
            extractor = DataExtractor(self.api_key_entry.get())
            raw = extractor.raw_generate(prompt, self.model_var.get())
            match = re.search(r'\{.*\}', raw or "", re.DOTALL)
            if match:
                new_data = self.clean_mapping(json.loads(match.group(0)))
                self.mapping.update(new_data); self.root.after(0, self.update_tree)
        except Exception as e: self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
        finally: self.root.after(0, lambda: self.refetch_btn.config(state="normal", text="REFETCH UNCHECKED FIELDS"))

    def iter_block_items(self, parent):
        parent_elm = parent.element.body if hasattr(parent, "element") and hasattr(parent.element, "body") else (parent._tc if isinstance(parent, _Cell) else parent._element)
        for child in parent_elm.iterchildren():
            if child.tag.endswith("}p"): yield Paragraph(child, parent)
            elif child.tag.endswith("}tbl"): yield Table(child, parent)

    def iter_paragraphs_deep(self, parent):
        for block in self.iter_block_items(parent):
            if isinstance(block, Paragraph): yield block
            elif isinstance(block, Table):
                for row in block.rows:
                    for cell in row.cells: yield from self.iter_paragraphs_deep(cell)

    def iter_story_parts(self, doc):
        yield "body", doc
        for section in doc.sections:
            for hf_attr in ['header', 'footer', 'first_page_header', 'first_page_footer', 'even_page_header', 'even_page_footer']:
                hf = getattr(section, hf_attr, None)
                if hf: yield hf_attr, hf

    def get_doc_content(self, doc):
        chunks = []
        for part_name, part in self.iter_story_parts(doc):
            for p in self.iter_paragraphs_deep(part):
                if p.text.strip(): chunks.append(f"[{part_name}] {p.text.strip()}")
        return "\n".join(chunks)

    def clean_mapping(self, mapping):
        if not isinstance(mapping, dict): return {}
        return {str(k).strip(): str(v).strip() for k, v in mapping.items() if k and v and "{{" in str(v)}

    def tag_exists(self, mapping, tag): return tag in " ".join(map(str, mapping.values()))

    def suggest_common_mappings(self, content, mapping):
        suggestions = {}; existing = {**mapping}
        # Simplified suggestion logic
        return self.clean_mapping(suggestions)

    def update_tree(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        for k, v in sorted(self.mapping.items(), key=lambda x: len(x[0]), reverse=True): self.tree.insert("", "end", values=(k, v))
        self.update_checklist_status()

    def add_manual(self):
        k, v = self.manual_key.get(), self.manual_tag.get()
        if k and v and "{{" in v: self.mapping[k] = v; self.update_tree()

    def delete_selected(self):
        for i in self.tree.selection():
            k = self.tree.item(i)['values'][0]
            if k in self.mapping: del self.mapping[k]
        self.update_tree()

    def generate_master(self):
        if not self.doc_path or not self.mapping: return
        doc = Document(self.doc_path); reps = sorted(self.mapping.items(), key=lambda x: len(x[0]), reverse=True)
        for _, part in self.iter_story_parts(doc):
            for p in self.iter_paragraphs_deep(part):
                for old, new in reps: self.safe_replace(p, old, new)
        save_p = filedialog.asksaveasfilename(defaultextension=".docx", initialfile="MASTER_TEMPLATE_READY.docx")
<<<<<<< HEAD
        if save_p:
            doc.save(save_p)
            messagebox.showinfo("Complete", f"Master Template saved!\n{len(reps)} placeholders applied.\nOriginal formatting preserved.")

    def apply_reps(self, p, reps):
        if not p.text.strip():
            return
        for old, new in reps:
            self.safe_replace_text_preserving_format(p, old, new)

    # ===================== FORMAT-PRESERVING REPLACEMENT ENGINE =====================

    def safe_replace_text_preserving_format(self, paragraph, old_text, new_text):
        """Replace without assigning paragraph.text, because that destroys Word run formatting."""
        if not old_text or old_text == new_text:
            return

        loop_guard = 50
        while loop_guard > 0:
            loop_guard -= 1
            match = self.find_fuzzy_match(paragraph, old_text)
            if not match:
                break

            start_r, start_off, end_r, end_off = match
            if start_r == end_r:
                rt = paragraph.runs[start_r].text
                paragraph.runs[start_r].text = rt[:start_off] + new_text + rt[end_off:]
            else:
                paragraph.runs[start_r].text = paragraph.runs[start_r].text[:start_off] + new_text
                for i in range(start_r + 1, end_r):
                    paragraph.runs[i].text = ""
                paragraph.runs[end_r].text = paragraph.runs[end_r].text[end_off:]

    def normalize_char(self, char):
        if char.isspace() or char == "\u00A0":
            return " "
        if char in ["\u2013", "\u2014", "\u2212", "–", "—", "−"]:
            return "-"
        if char in ["‘", "’", "`", "´"]:
            return "'"
        if char in ["“", "”", "„", "‟"]:
            return '"'
        return char

    def normalize_for_match(self, value):
        if not value:
            return ""
        normalized_chars = [self.normalize_char(c) for c in value]
        val = "".join(normalized_chars)
        return re.sub(r"[\s\u00A0]+", " ", val).strip().casefold()

    def is_ignored_compact_char(self, char):
        return char.isspace() or char in ["-", "\u2013", "\u2014", "\u2212", "–", "—", "−"]

    def find_fuzzy_match(self, paragraph, needle):
        if not paragraph.runs:
            return None

        chars = []
        positions = []
        for run_idx, run in enumerate(paragraph.runs):
            for char_idx, char in enumerate(run.text):
                chars.append(self.normalize_char(char))
                positions.append((run_idx, char_idx))

        haystack = "".join(chars)
        target = self.normalize_for_match(needle)
        if not haystack or not target:
            return None

        pattern = re.escape(target).replace(r"\ ", r"[\s\u00A0]+")
        try:
            match = re.search(pattern, haystack, re.IGNORECASE | re.DOTALL)
        except re.error:
            match = None
=======
        if save_p: doc.save(save_p); messagebox.showinfo("Done", "Template generated!")
>>>>>>> 3c8ef3700876862f09e11a95b6a2e9e767d3567e

    def safe_replace(self, p, old, new):
        if not old or old == new: return
        match = self.find_fuzzy_match(p, old)
        if match:
<<<<<<< HEAD
            return self.match_to_run_offsets(positions, match.start(), match.end())

        compact_chars = []
        compact_positions = []
        for idx, char in enumerate(haystack):
            if not self.is_ignored_compact_char(char):
                compact_chars.append(char)
                compact_positions.append(idx)

        compact_target = "".join([c for c in target if not self.is_ignored_compact_char(c)])
        if not compact_target:
            return None

        found_at = "".join(compact_chars).casefold().find(compact_target)
        if found_at == -1:
            return None

        start = compact_positions[found_at]
        end = compact_positions[found_at + len(compact_target) - 1] + 1
        return self.match_to_run_offsets(positions, start, end)

    def match_to_run_offsets(self, positions, start, end):
        if start >= end or start >= len(positions):
            return None
        end = min(end, len(positions))
        start_r, start_off = positions[start]
        end_r, end_last_off = positions[end - 1]
        return start_r, start_off, end_r, end_last_off + 1
=======
            s_r, s_o, e_r, e_o = match
            if s_r == e_r: p.runs[s_r].text = p.runs[s_r].text[:s_o] + new + p.runs[s_r].text[e_o:]
            else:
                p.runs[s_r].text = p.runs[s_r].text[:s_o] + new
                for i in range(s_r + 1, e_r): p.runs[i].text = ""
                p.runs[e_r].text = p.runs[e_r].text[e_o:]
>>>>>>> 3c8ef3700876862f09e11a95b6a2e9e767d3567e

    def find_fuzzy_match(self, p, needle):
        if not p.runs: return None
        chars = []; pos = []
        for ri, run in enumerate(p.runs):
            for ci, c in enumerate(run.text): chars.append(" " if c.isspace() or c=="\u00A0" else c); pos.append((ri, ci))
        haystack = "".join(chars); target = re.sub(r"[\s\u00A0]+", " ", needle).strip().casefold()
        pattern = re.escape(target).replace(r"\ ", r"[\s\u00A0]+")
        m = re.search(pattern, haystack, re.IGNORECASE)
        if m:
            s, e = m.start(), m.end(); sr, so = pos[s]; er, eo = pos[e-1]; return sr, so, er, eo + 1
        return None

if __name__ == "__main__":
    root = tk.Tk(); TemplateBuilder(root); root.mainloop()
