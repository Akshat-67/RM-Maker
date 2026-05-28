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

DEFAULT_API_KEY = os.getenv("GEMINI_API_KEY") or "AIzaSyDs32YIJx35FDhb9qOa3vTcWDtU-RpL5_w"

class TemplateBuilder:
    def __init__(self, root):
        self.root = root
        self.root.title("LegalDoc Master Template Creator v5")
        self.root.geometry("1450x980")

        self.doc_path = ""
        self.mapping = {}  # {exact_text_from_doc: {{jinja2_tag}}}

        # All available placeholder tags for the manual mapping dropdown
        self.all_tags = [
            ("RM Execution Date", "{{rd}}"),
            ("Loan Agreement Date", "{{ad}}"),
            ("Borrower 1 - Salutation", "{{bs[0].s}}"),
            ("Borrower 1 - Name", "{{bs[0].n}}"),
            ("Borrower 1 - Age", "{{bs[0].a}}"),
            ("Borrower 1 - Relation", "{{bs[0].r}}"),
            ("Borrower 1 - Rel Name", "{{bs[0].rn}}"),
            ("Borrower 1 - Address", "{{bs[0].adr}}"),
            ("Borrower 1 - Aadhar/ID", "{{bs[0].id}}"),
            ("Borrower 2 - Name", "{{bs[1].n}}"),
            ("Borrower 2 - Relation", "{{bs[1].r}}"),
            ("Borrower 2 - Rel Name", "{{bs[1].rn}}"),
            ("Borrower 2 - Address", "{{bs[1].adr}}"),
            ("Borrower 2 - Aadhar/ID", "{{bs[1].id}}"),
            ("Borrower 3 - Name", "{{bs[2].n}}"),
            ("Borrower 3 - Relation", "{{bs[2].r}}"),
            ("Borrower 3 - Rel Name", "{{bs[2].rn}}"),
            ("Borrower 3 - Address", "{{bs[2].adr}}"),
            ("Borrower 3 - Aadhar/ID", "{{bs[2].id}}"),
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
            ("Bank Signatory - Relation", "{{bsign.r}}"),
            ("Bank Signatory - Rel Name", "{{bsign.rn}}"),
            ("Witness 1 - Name", "{{ws[0].n}}"),
            ("Witness 1 - Relation", "{{ws[0].r}}"),
            ("Witness 1 - Rel Name", "{{ws[0].rn}}"),
            ("Witness 1 - Address", "{{ws[0].adr}}"),
            ("Witness 2 - Name", "{{ws[1].n}}"),
            ("Witness 2 - Relation", "{{ws[1].r}}"),
            ("Witness 2 - Rel Name", "{{ws[1].rn}}"),
            ("Witness 2 - Address", "{{ws[1].adr}}"),
            ("Document Schedule / Title Chain (FIRST SCHEDULE)", "{{ds_text}}"),
            ("Second Schedule (Documents to be collected)", "{{second_schedule}}"),
        ]

        self.available_models = []
        self.model_var = tk.StringVar(value="gemini-1.5-flash")

        self.setup_ui()
        # Auto-fetch models in background
        threading.Thread(target=self._auto_fetch_models, daemon=True).start()

    def _auto_fetch_models(self):
        """Fetch available Gemini models on startup."""
        try:
            extractor = DataExtractor(DEFAULT_API_KEY)
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

    def setup_ui(self):
        # Color Palette
        self.c_bg = "#F3F4F6"
        self.c_panel = "#FFFFFF"
        self.c_blue = "#1A73E8"
        self.c_success = "#0F9D58"
        self.c_danger = "#D93025"
        self.c_border = "#DADCE0"
        self.c_text = "#3C4043"

        self.root.configure(bg=self.c_bg)

        # Header
        header = tk.Frame(self.root, bg=self.c_blue, height=70)
        header.pack(fill="x")
        tk.Label(header, text="MASTER TEMPLATE GENERATOR PRO v5", fg="white", bg=self.c_blue, font=("Segoe UI", 18, "bold"), padx=25).pack(side="left")
        tk.Label(header, text="Format-Preserving AI Template Builder", fg="#E8F0FE", bg=self.c_blue, font=("Segoe UI", 10, "italic")).pack(side="right", padx=25)

        main_content = tk.Frame(self.root, bg=self.c_bg)
        main_content.pack(fill="both", expand=True, padx=20, pady=15)

        # ============ LEFT PANEL: Config & Mapping Tree ============
        left_panel = tk.Frame(main_content, bg=self.c_bg, width=480)
        left_panel.pack(side="left", fill="y", padx=(0, 10))
        left_panel.pack_propagate(False)

        # 1. Source Document
        group1 = tk.LabelFrame(left_panel, text=" 1. SELECT COMPLETED RM DOCUMENT ", bg=self.c_panel, font=("Segoe UI", 10, "bold"), padx=15, pady=15, fg=self.c_blue)
        group1.pack(fill="x", pady=(0, 10))
        tk.Button(group1, text="OPEN .DOCX FILE", command=self.load_doc, bg=self.c_blue, fg="white", bd=0, pady=12, font=("Segoe UI", 10, "bold"), cursor="hand2").pack(fill="x")
        self.path_lbl = tk.Label(group1, text="No file selected", fg="#70757A", bg=self.c_panel, font=("Segoe UI", 9))
        self.path_lbl.pack(pady=8)

        # 2. AI Config (pre-filled API key + model)
        group2 = tk.LabelFrame(left_panel, text=" 2. AI CONFIGURATION ", bg=self.c_panel, font=("Segoe UI", 10, "bold"), padx=15, pady=15, fg=self.c_blue)
        group2.pack(fill="x", pady=10)

        tk.Label(group2, text="API Key (auto-filled):", bg=self.c_panel, font=("Segoe UI", 9)).pack(anchor="w")
        self.api_key_entry = tk.Entry(group2, show="*", bg="#F1F3F4", bd=0, font=("Consolas", 10))
        self.api_key_entry.insert(0, DEFAULT_API_KEY)
        self.api_key_entry.pack(fill="x", ipady=8, pady=5)

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

    def load_doc(self):
        p = filedialog.askopenfilename(filetypes=[("Word Document", "*.docx")])
        if p:
            if not p.lower().endswith(".docx"):
                messagebox.showwarning("Unsupported Format", "Please select a .docx file.")
                return
            self.doc_path = p
            self.path_lbl.config(text=os.path.basename(p), fg=self.c_blue)

    # ===================== AI DISCOVERY =====================

    def discover_data(self):
        if not self.doc_path: messagebox.showwarning("Missing File", "Please select a completed RM Word Document first."); return
        self.discover_btn.config(state="disabled", text="AI IS SCANNING DOCUMENT...")
        threading.Thread(target=self.run_ai_discovery).start()

    def run_ai_discovery(self):
        try:
            doc = Document(self.doc_path)
            content = self.get_doc_content(doc)

            prompt = f"""
            CRITICAL MISSION: CONVERT COMPLETED DOCUMENT TO MASTER JINJA2 TEMPLATE.
            You are an expert legal document analyst. Your goal is 100% discovery of variable data.
            Identify ALL case-specific variable fields in the text below and map them to our system tags.

            CORE TAG SCHEMA:
            - rd: RM Execution Date (e.g., '10th day of May 2024')
            - ad: Loan Agreement Date (e.g., '15.04.2024')
            - bs[i]: Borrowers list. s=Salutation, n=Name, a=Age, r=Relation, rn=Rel Name, adr=Address, id=Aadhar/ID
            - ls[i]: Loans list. n=LAN No, a=Amount in Figures, w=Amount in Words, t=Tenure
            - ps[i]: Property schedules. adr=Address, n=North, s=South, e=East, w=West
            - bsign: Bank Signatory. n=Name, r=Relation, rn=Relative Name
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
               - full property address/schedule and all boundaries
               - loan tenure such as 120 Months, 180 Months, 240 Months
            6. If a line reads like "Mr. Ram Kumar S/o Shyam Lal R/o Jaipur", map it separately:
               {{"Mr. Ram Kumar": "{{{{bs[0].s}}}} {{{{bs[0].n}}}}", "S/o Shyam Lal": "{{{{bs[0].r}}}} {{{{bs[0].rn}}}}"}}

            Return ONLY a valid JSON dictionary. No preamble.

            DOCUMENT TEXT:
            {content}
            """

            extractor = DataExtractor(self.api_key_entry.get())
            raw = extractor.raw_generate(prompt, self.model_var.get())
            if not raw:
                self.root.after(0, lambda: messagebox.showerror("AI Error", "AI returned an empty response."))
                return
            match = re.search(r'\{.*\}', raw, re.DOTALL)
            if match:
                self.mapping = self.clean_mapping(json.loads(match.group(0)))
                self.root.after(0, self.update_ui)
                self.root.after(0, lambda: messagebox.showinfo("Success", f"AI found {len(self.mapping)} variable fields!"))
            else:
                self.root.after(0, lambda: messagebox.showerror("AI Error", "AI failed to generate a valid mapping structure."))
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda msg=error_msg: messagebox.showerror("System Error", msg))
        finally:
            self.root.after(0, lambda: self.discover_btn.config(state="normal", text="🔍 START AI DISCOVERY"))

    # ===================== DOCUMENT PARSING =====================

    def iter_block_items(self, parent):
        if hasattr(parent, "element") and hasattr(parent.element, "body"):
            parent_elm = parent.element.body
        elif isinstance(parent, _Cell):
            parent_elm = parent._tc
        else:
            parent_elm = parent._element

        for child in parent_elm.iterchildren():
            if child.tag.endswith("}p"):
                yield Paragraph(child, parent)
            elif child.tag.endswith("}tbl"):
                yield Table(child, parent)

    def iter_paragraphs_deep(self, parent):
        for block in self.iter_block_items(parent):
            if isinstance(block, Paragraph):
                yield block
            elif isinstance(block, Table):
                for row in block.rows:
                    for cell in row.cells:
                        yield from self.iter_paragraphs_deep(cell)

    def iter_story_parts(self, doc):
        yield "body", doc
        for section in doc.sections:
            for hf_attr in ['header', 'footer', 'first_page_header', 'first_page_footer', 'even_page_header', 'even_page_footer']:
                hf = getattr(section, hf_attr, None)
                if hf:
                    yield hf_attr, hf

    def get_doc_content(self, doc):
        chunks = []
        for part_name, part in self.iter_story_parts(doc):
            for p in self.iter_paragraphs_deep(part):
                text = p.text.strip()
                if text:
                    chunks.append(f"[{part_name}] {text}")
        return "\n".join(chunks)

    # ===================== MAPPING UTILITIES =====================

    def clean_mapping(self, mapping):
        if not isinstance(mapping, dict):
            return {}

        cleaned = {}
        for old, new in mapping.items():
            old = "" if old is None else str(old).strip()
            new = "" if new is None else str(new).strip()
            if not old or not new or old == new:
                continue
            if "{{" not in new or "}}" not in new:
                continue
            cleaned[old] = new
        return cleaned

    # ===================== UI UPDATES =====================

    def update_ui(self):
        """Update the tree, verification list, and count label."""
        self.update_tree()
        self.update_verification_list()
        self.mapping_count_label.config(text=f"Total mappings: {len(self.mapping)}")

    def update_tree(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        sorted_map = sorted(self.mapping.items(), key=lambda x: len(x[0]), reverse=True)
        for k, v in sorted_map:
            self.tree.insert("", "end", values=(k, v))

    def update_verification_list(self):
        """Show all mappings with remove buttons."""
        for w in self.ver_frame.winfo_children(): w.destroy()
        if not self.mapping:
            tk.Label(self.ver_frame, text="No mappings yet. Run AI discovery or add manually.", bg=self.c_panel, fg="#9AA0A6", font=("Segoe UI", 9)).pack(pady=20)
            return
        sorted_map = sorted(self.mapping.items(), key=lambda x: len(x[0]), reverse=True)
        for old_text, tag in sorted_map:
            row_f = tk.Frame(self.ver_frame, bg=self.c_panel)
            row_f.pack(fill="x", pady=2, padx=5)
            row_f.config(highlightthickness=1, highlightbackground="#E8EAED")

            # Green checkmark for found
            tk.Label(row_f, text="✅", bg=self.c_panel).pack(side="left", padx=5)
            tk.Label(row_f, text=f'"{old_text}"  →  {tag}', bg=self.c_panel, fg=self.c_text, font=("Segoe UI", 9), anchor="w", wraplength=420).pack(side="left", fill="x", expand=True, padx=5)
            tk.Button(row_f, text="✖", font=("Segoe UI", 8, "bold"), bg=self.c_panel, fg=self.c_danger,
                     bd=0, cursor="hand2",
                     command=lambda ot=old_text: self.remove_mapping(ot)).pack(side="right", padx=5)

    def remove_mapping(self, old_text):
        if old_text in self.mapping:
            del self.mapping[old_text]
        self.update_ui()

    # ===================== MANUAL MAPPING =====================

    def add_manual(self):
        text = self.manual_text_entry.get().strip()
        display_val = self.manual_tag_dropdown.get().strip()

        if not text:
            messagebox.showwarning("Missing Text", "Enter the exact text from the document first.")
            return
        if not display_val:
            messagebox.showwarning("Missing Tag", "Select a placeholder tag from the dropdown.")
            return

        # Extract the tag from the display value: "Borrower 1 - Name  →  {{bs[0].n}}"
        tag_match = re.search(r'(\{\{.*?\}\})', display_val)
        if not tag_match:
            messagebox.showerror("Error", "Could not parse tag from selection.")
            return
        tag = tag_match.group(1)

        self.mapping[text] = tag
        self.manual_text_entry.delete(0, tk.END)
        self.manual_tag_dropdown.set("")
        self.update_ui()

    def delete_selected(self):
        for i in self.tree.selection():
            k = self.tree.item(i)['values'][0]
            if k in self.mapping:
                del self.mapping[k]
        self.update_ui()

    def clear_all(self):
        if messagebox.askyesno("Clear All", "Remove all mappings?"):
            self.mapping = {}
            self.update_ui()

    # ===================== GENERATE MASTER TEMPLATE =====================

    def generate_master(self):
        if not self.doc_path:
            messagebox.showwarning("Warning", "No source document selected.")
            return
        if not self.mapping:
            messagebox.showwarning("Warning", "No mappings to apply. Run AI discovery or add mappings manually.")
            return

        doc = Document(self.doc_path)
        reps = sorted(self.clean_mapping(self.mapping).items(), key=lambda x: len(x[0]), reverse=True)

        for _, part in self.iter_story_parts(doc):
            for p in self.iter_paragraphs_deep(part):
                self.apply_reps(p, reps)

        save_p = filedialog.asksaveasfilename(defaultextension=".docx", initialfile="MASTER_TEMPLATE_READY.docx")
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

    def normalize_for_match(self, value):
        return re.sub(r"[\s\u00A0]+", " ", value or "").strip().casefold()

    def find_fuzzy_match(self, paragraph, needle):
        if not paragraph.runs:
            return None

        chars = []
        positions = []
        for run_idx, run in enumerate(paragraph.runs):
            for char_idx, char in enumerate(run.text):
                chars.append(" " if char.isspace() or char == "\u00A0" else char)
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

        if match:
            return self.match_to_run_offsets(positions, match.start(), match.end())

        compact_chars = []
        compact_positions = []
        for idx, char in enumerate(haystack):
            if not char.isspace():
                compact_chars.append(char)
                compact_positions.append(idx)

        compact_target = re.sub(r"[\s\u00A0]+", "", target)
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


if __name__ == "__main__":
    root = tk.Tk()
    TemplateBuilder(root)
    root.mainloop()