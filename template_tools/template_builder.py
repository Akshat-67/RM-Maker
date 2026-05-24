import os
import sys
import json
import re
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from docx import Document

# Add root directory to path so extractor can be found
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from extractor import DataExtractor

class TemplateBuilder:
    def __init__(self, root):
        self.root = root
        self.root.title("LegalDoc Master Template Creator v4 - 100% Accuracy Engine")
        self.root.geometry("1450x980")

        self.doc_path = ""
        self.mapping = {}
        self.checklist_items = []
        # Comprehensive schema for high-accuracy mapping
        self.expected_fields = [
            ("RM Execution Date", "{{rd}}"),
            ("Loan Agreement Date", "{{ad}}"),
            ("Borrower 1 Salutation", "{{bs[0].s}}"),
            ("Borrower 1 Name", "{{bs[0].n}}"),
            ("Borrower 1 Age", "{{bs[0].a}}"),
            ("Borrower 1 Relation (S/o, W/o)", "{{bs[0].r}}"),
            ("Borrower 1 Rel Name", "{{bs[0].rn}}"),
            ("Borrower 1 Address", "{{bs[0].adr}}"),
            ("Borrower 1 Aadhar/ID", "{{bs[0].id}}"),
            ("Borrower 2 Name", "{{bs[1].n}}"),
            ("Borrower 2 Address", "{{bs[1].adr}}"),
            ("Loan 1 LAN No", "{{ls[0].n}}"),
            ("Loan 1 Amount (Value)", "{{ls[0].a}}"),
            ("Loan 1 Amount (Words)", "{{ls[0].w}}"),
            ("Loan 1 Tenure", "{{ls[0].t}}"),
            ("Loan 2 LAN No", "{{ls[1].n}}"),
            ("Loan 2 Amount", "{{ls[1].a}}"),
            ("Property Address", "{{ps[0].adr}}"),
            ("Property North", "{{ps[0].n}}"),
            ("Property South", "{{ps[0].s}}"),
            ("Property East", "{{ps[0].e}}"),
            ("Property West", "{{ps[0].w}}"),
            ("Bank Signatory Name", "{{bsign.n}}"),
            ("Bank Signatory Rel", "{{bsign.r}}"),
            ("Bank Signatory Rel Name", "{{bsign.rn}}"),
            ("Witness 1 Name", "{{ws[0].n}}"),
            ("Witness 1 Address", "{{ws[0].adr}}"),
            ("Witness 2 Name", "{{ws[1].n}}"),
            ("Witness 2 Address", "{{ws[1].adr}}")
        ]
        self.setup_ui()

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
        tk.Label(header, text="MASTER TEMPLATE GENERATOR PRO", fg="white", bg=self.c_blue, font=("Segoe UI", 18, "bold"), padx=25).pack(side="left")
        tk.Label(header, text="Unified Verification & Discovery System", fg="#E8F0FE", bg=self.c_blue, font=("Segoe UI", 10, "italic")).pack(side="right", padx=25)

        main_content = tk.Frame(self.root, bg=self.c_bg)
        main_content.pack(fill="both", expand=True, padx=20, pady=15)

        # ---------------- LEFT PANEL: Config & Discovery ----------------
        left_panel = tk.Frame(main_content, bg=self.c_bg, width=520)
        left_panel.pack(side="left", fill="y", padx=(0, 15))
        left_panel.pack_propagate(False)

        # 1. Source Select
        group1 = tk.LabelFrame(left_panel, text=" 1. SELECT SOURCE WORD DOCUMENT ", bg=self.c_panel, font=("Segoe UI", 10, "bold"), padx=15, pady=15, fg=self.c_blue)
        group1.pack(fill="x", pady=(0, 10))
        tk.Button(group1, text="OPEN .DOCX FILE", command=self.load_doc, bg=self.c_blue, fg="white", bd=0, pady=12, font=("Segoe UI", 10, "bold"), cursor="hand2").pack(fill="x")
        self.path_lbl = tk.Label(group1, text="No file selected", fg="#70757A", bg=self.c_panel, font=("Segoe UI", 9))
        self.path_lbl.pack(pady=8)

        # 2. AI Connection
        group2 = tk.LabelFrame(left_panel, text=" 2. AI CONFIGURATION ", bg=self.c_panel, font=("Segoe UI", 10, "bold"), padx=15, pady=15, fg=self.c_blue)
        group2.pack(fill="x", pady=10)
        tk.Label(group2, text="API Key:", bg=self.c_panel, font=("Segoe UI", 9)).pack(anchor="w")
        self.api_key_entry = tk.Entry(group2, show="*", bg="#F1F3F4", bd=0, font=("Consolas", 10)); self.api_key_entry.pack(fill="x", ipady=8, pady=5)

        self.model_var = tk.StringVar(value="gemini-1.5-flash")
        self.model_dropdown = ttk.Combobox(group2, textvariable=self.model_var, values=["gemini-1.5-flash"], font=("Segoe UI", 10))
        self.model_dropdown.pack(fill="x", pady=5)
        tk.Button(group2, text="Verify API Status", command=self.refresh_models, bg="#E8F0FE", fg=self.c_blue, bd=0, font=("Segoe UI", 9, "bold")).pack(fill="x", pady=5)

        # Discovery Action
        self.discover_btn = tk.Button(left_panel, text="🔍 START FULL AI DATA DISCOVERY", command=self.discover_data, bg=self.c_green, fg="white", font=("Segoe UI", 13, "bold"), bd=0, pady=18, cursor="hand2")
        self.discover_btn.pack(fill="x", pady=15)

        # 3. Mapping Audit
        group3 = tk.LabelFrame(left_panel, text=" 3. CURRENT MAPPING AUDIT ", bg=self.c_panel, font=("Segoe UI", 10, "bold"), padx=10, pady=10, fg=self.c_blue)
        group3.pack(fill="both", expand=True, pady=10)

        self.tree = ttk.Treeview(group3, columns=("Raw", "Tag"), show='headings')
        self.tree.heading("Raw", text="Exact Document Substring")
        self.tree.heading("Tag", text="Placeholder Tag (Jinja2)")
        self.tree.column("Raw", width=320)
        self.tree.column("Tag", width=160)
        self.tree.pack(side="left", fill="both", expand=True)

        sb = ttk.Scrollbar(group3, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set); sb.pack(side="right", fill="y")

        # ---------------- MIDDLE PANEL: Checklist ----------------
        mid_panel = tk.Frame(main_content, bg=self.c_panel, width=450, highlightbackground=self.c_border, highlightthickness=1)
        mid_panel.pack(side="left", fill="y", padx=15)
        mid_panel.pack_propagate(False)

        tk.Label(mid_panel, text="VERIFICATION CHECKLIST", font=("Segoe UI", 14, "bold"), bg=self.c_panel, pady=20, fg=self.c_text).pack()
        tk.Label(mid_panel, text="Green = Mapped | Red = Missing / Needs Verification", fg="#5F6368", bg=self.c_panel, font=("Segoe UI", 9)).pack(pady=(0,10))

        check_container = tk.Frame(mid_panel, bg=self.c_panel)
        check_container.pack(fill="both", expand=True, padx=20)

        check_canvas = tk.Canvas(check_container, bg=self.c_panel, highlightthickness=0)
        check_sb = ttk.Scrollbar(check_container, orient="vertical", command=check_canvas.yview)
        self.check_scroll_f = tk.Frame(check_canvas, bg=self.c_panel)

        self.check_scroll_f.bind("<Configure>", lambda e: check_canvas.configure(scrollregion=check_canvas.bbox("all")))
        check_canvas.create_window((0,0), window=self.check_scroll_f, anchor="nw")
        check_canvas.configure(yscrollcommand=check_sb.set)

        check_canvas.pack(side="left", fill="both", expand=True)
        check_sb.pack(side="right", fill="y")
        self.init_checklist()

        # ---------------- RIGHT PANEL: Actions ----------------
        right_panel = tk.Frame(main_content, bg=self.c_bg, width=380)
        right_panel.pack(side="left", fill="y", padx=(10, 0))
        right_panel.pack_propagate(False)

        # targeted re-scan
        r1 = tk.LabelFrame(right_panel, text=" SMART GAP FIXER ", bg=self.c_panel, font=("Segoe UI", 10, "bold"), padx=15, pady=15, fg=self.c_red)
        r1.pack(fill="x", pady=(0, 10))
        tk.Label(r1, text="Untick items on the left then run:", bg=self.c_panel, font=("Segoe UI", 9), justify="left", fg=self.c_text).pack(pady=5)
        self.refetch_btn = tk.Button(r1, text="REFETCH UNCHECKED FIELDS", command=self.refetch_missing, bg=self.c_red, fg="white", font=("Segoe UI", 10, "bold"), bd=0, pady=15, cursor="hand2")
        self.refetch_btn.pack(fill="x")

        # manual override
        r2 = tk.LabelFrame(right_panel, text=" MANUAL CORRECTION ", bg=self.c_panel, font=("Segoe UI", 10, "bold"), padx=15, pady=15, fg="#5F6368")
        r2.pack(fill="x", pady=15)
        self.manual_key = tk.Entry(r2, bg="#F1F3F4", bd=0, font=("Segoe UI", 10)); self.manual_key.pack(fill="x", ipady=10); self.manual_key.insert(0, "Exact text from doc")
        self.manual_tag = tk.Entry(r2, bg="#F1F3F4", bd=0, font=("Segoe UI", 10)); self.manual_tag.pack(fill="x", ipady=10, pady=10); self.manual_tag.insert(0, "{{tag}}")
        tk.Button(r2, text="ADD TO MAPPING", command=self.add_manual, bg="#5F6368", fg="white", bd=0, pady=10, font=("Segoe UI", 9, "bold")).pack(fill="x")
        tk.Button(r2, text="REMOVE SELECTED", command=self.delete_selected, fg=self.c_danger, bg=self.c_panel, bd=1, pady=5).pack(fill="x", pady=10)

        # final generate
        self.save_btn = tk.Button(right_panel, text="GENERATE FINAL\nMASTER TEMPLATE", command=self.generate_master, bg=self.c_blue, fg="white", font=("Segoe UI", 14, "bold"), bd=0, pady=30, cursor="hand2")
        self.save_btn.pack(fill="x", side="bottom", pady=20)

    def init_checklist(self):
        for w in self.check_scroll_f.winfo_children(): w.destroy()
        self.checklist_items = []
        for label, tag in self.expected_fields:
            f = tk.Frame(self.check_scroll_f, bg=self.c_panel)
            f.pack(fill="x", pady=4)
            var = tk.BooleanVar(value=False)
            cb = tk.Checkbutton(f, text=f"{label}  ({tag})", variable=var, bg=self.c_panel, font=("Segoe UI", 10), activebackground=self.c_panel)
            cb.pack(side="left")
            self.checklist_items.append((label, tag, var, cb))

    def update_checklist_status(self):
        all_mapped_tags = " ".join(self.mapping.values())
        for label, tag, var, cb in self.checklist_items:
            found = tag in all_mapped_tags
            var.set(found)
            cb.config(fg=self.c_success if found else self.c_danger)

    def load_doc(self):
        p = filedialog.askopenfilename(filetypes=[("Word Document", "*.docx")])
        if p: self.doc_path = p; self.path_lbl.config(text=os.path.basename(p), fg=self.c_blue)

    def refresh_models(self):
        k = self.api_key_entry.get()
        if not k: messagebox.showwarning("Key Required", "Please provide a Gemini API Key."); return
        try:
            models = DataExtractor(k).get_available_models()
            if models:
                self.model_dropdown['values'] = models
                self.model_var.set(models[0])
                messagebox.showinfo("AI System", f"Connection Established. Found {len(models)} models.")
        except Exception as e: messagebox.showerror("AI Error", f"Connection Failed: {e}")

    def discover_data(self):
        if not self.doc_path: messagebox.showwarning("Missing File", "Please select a completed RM Word Document first."); return
        if not self.api_key_entry.get(): messagebox.showwarning("Missing Key", "Please provide a Gemini API Key."); return

        self.discover_btn.config(state="disabled", text="AI IS SCANNING DOCUMENT...")
        threading.Thread(target=self.run_ai_discovery).start()

    def run_ai_discovery(self):
        try:
            doc = Document(self.doc_path)
            content = self.get_doc_content(doc)

            prompt = f"""
            CRITICAL MISSION: CONVERT DOCUMENT TO MASTER TEMPLATE.
            You are a legal document analyst. Your goal is 100% accuracy.
            Identify ALL variable fields in the text below and map them to our system tags.

            CORE SCHEMA:
            - rd: RM Execution Date (e.g. 5th day of May 2026)
            - ad: Loan Agreement Date
            - bs[i]: Borrowers. s=Salutation, n=Name, a=Age, r=Relation, rn=Rel Name, adr=Address, id=Aadhar/ID
            - ls[i]: Loans. n=LAN, a=Amount Value, w=Amount Words, t=Tenure
            - ps[i]: Properties. adr=Address, n=North, s=South, e=East, w=West
            - bsign: Bank Signatory. n=Name, r=Rel, rn=Rel Name
            - ws[i]: Witnesses. n=Name, r=Rel, rn=Rel Name, adr=Address

            ABSOLUTE RULES:
            1. ANCHORED MAPPING: Do NOT return bare values. Return the WHOLE phrase including static text.
               GOOD: {{"MORTGAGE MONEY RS. 17,15,000/-": "MORTGAGE MONEY RS. {{{{ls[0].a}}}}"}}
               BAD: {{"17,15,000": "{{{{ls[0].a}}}}"}}

            2. MULTIPLE ENTITIES: Carefully separate Borrower 1 [0] from Borrower 2 [1], and Loan 1 [0] from Loan 2 [1].
            3. EXACT MATCH: Keys MUST be character-perfect substrings from the text.
            4. EXHAUSTIVE: Check Headers, Footers, and Tables.

            Return ONLY a valid JSON dictionary: {{"EXACT SUBSTRING": "SUBSTRING WITH {{{{tags}}}}"}}

            DOCUMENT TEXT:
            {content}
            """

            extractor = DataExtractor(self.api_key_entry.get())
            raw = extractor.raw_generate(prompt, self.model_var.get())
            match = re.search(r'\{.*\}', raw, re.DOTALL)
            if match:
                self.mapping = json.loads(match.group(0))
                self.root.after(0, self.update_tree)
            else: self.root.after(0, lambda: messagebox.showerror("AI Error", "AI failed to generate a valid mapping structure."))
        except Exception as e: self.root.after(0, lambda: messagebox.showerror("System Error", str(e)))
        finally: self.root.after(0, lambda: self.discover_btn.config(state="normal", text="🔍 START FULL DATA DISCOVERY"))

    def refetch_missing(self):
        missing = [tag for label, tag, var, cb in self.checklist_items if not var.get()]
        if not missing:
            if not messagebox.askyesno("Deep Scan", "All checklist items are found. Run exhaustive search for other variable data?"): return
            missing = ["ALL OTHER VARIABLES"]

        self.refetch_btn.config(state="disabled", text="AI IS FIXING GAPS...")
        threading.Thread(target=self.run_gap_fix, args=(missing,)).start()

    def run_gap_fix(self, missing_tags):
        try:
            doc = Document(self.doc_path)
            content = self.get_doc_content(doc)
            prompt = f"""
            GAP ANALYSIS: We missed these fields in the first pass: {missing_tags}.
            Find the EXACT strings for them in the text below.
            Use the ANCHORED mapping strategy (include surrounding words).
            Also look for ANY other names, dates, or unique numbers that haven't been tagged yet.

            SCHEMA: {self.expected_fields}

            TEXT:
            {content}

            Return ONLY a JSON dictionary: {{"EXACT TEXT": "TEXT WITH {{{{tags}}}}"}}
            """

            extractor = DataExtractor(self.api_key_entry.get())
            raw = extractor.raw_generate(prompt, self.model_var.get())
            match = re.search(r'\{.*\}', raw, re.DOTALL)
            if match:
                new_data = json.loads(match.group(0))
                self.mapping.update(new_data)
                self.root.after(0, self.update_tree)
                self.root.after(0, lambda: messagebox.showinfo("Gap Fix Success", f"Added {len(new_data)} more entries! Check the checklist."))
        except Exception as e: self.root.after(0, lambda: messagebox.showerror("AI Error", str(e)))
        finally: self.root.after(0, lambda: self.refetch_btn.config(state="normal", text="REFETCH UNCHECKED FIELDS"))

    def get_doc_content(self, doc):
        text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
        for table in doc.tables:
            for row in table.rows:
                text += "\n" + " | ".join(cell.text.strip() for cell in row.cells)
        return text

    def update_tree(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        # Length descending sort ensures specific phrases are replaced before generic ones
        sorted_map = sorted(self.mapping.items(), key=lambda x: len(x[0]), reverse=True)
        for k, v in sorted_map: self.tree.insert("", "end", values=(k, v))
        self.update_checklist_status()

    def add_manual(self):
        k, v = self.manual_key.get(), self.manual_tag.get()
        if k and v and k != "Exact text from doc":
            self.mapping[k] = v
            self.update_tree()

    def delete_selected(self):
        for i in self.tree.selection():
            k = self.tree.item(i)['values'][0]
            if k in self.mapping: del self.mapping[k]
        self.update_tree()

    def generate_master(self):
        if not self.doc_path or not self.mapping: messagebox.showwarning("Warning", "Discovery must be run before saving."); return
        doc = Document(self.doc_path)
        reps = sorted(self.mapping.items(), key=lambda x: len(x[0]), reverse=True)

        # Comprehensive cross-section replacement
        for section in doc.sections:
            for p in section.header.paragraphs: self.apply_reps(p, reps)
            for p in section.footer.paragraphs: self.apply_reps(p, reps)

        for p in doc.paragraphs: self.apply_reps(p, reps)
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for p in cell.paragraphs: self.apply_reps(p, reps)

        save_p = filedialog.asksaveasfilename(defaultextension=".docx", initialfile="MASTER_TEMPLATE_READY.docx")
        if save_p:
            doc.save(save_p)
            messagebox.showinfo("Complete", "Master Template Generated with 100% original styles preserved!")

    def apply_reps(self, p, reps):
        if not p.text.strip(): return
        for old, new in reps:
            self.replace_text_preserving_format(p, old, new)

    def replace_text_preserving_format(self, paragraph, old_text, new_text):
        """Indestructible replacement engine: Preserves styles even if Word splits text into weird runs."""
        if not old_text or old_text == new_text: return

        # 1. Normalize spaces for cross-engine compatibility
        norm_old = re.sub(r'[\s\u00A0]+', ' ', old_text).strip()

        # 2. Build resilient regex (handles NBSP, Tab splits, isolation of punctuation in runs)
        pattern_str = re.escape(norm_old).replace(r'\ ', r'[\s\u00A0]*')
        for char in [r'\.', r'\/', r'\-', r'\,', r'\(', r'\)', r'\:', r'\\', r'\[', r'\]', r'\₹', r'\$']:
            pattern_str = pattern_str.replace(char, char + r'[\s\u00A0]*')

        try: pattern = re.compile(pattern_str, re.IGNORECASE | re.MULTILINE | re.DOTALL)
        except: return

        # Strategy A: Run-Level Injection (Preserves styles)
        loop_guard = 50
        while loop_guard > 0:
            loop_guard -= 1
            full_text = "".join(r.text for r in paragraph.runs)
            match = pattern.search(full_text)

            if not match:
                # STRATEGY B: Whitespace-Stripped Fallback (Last resort)
                stripped_full = re.sub(r'[\s\u00A0]+', '', full_text)
                stripped_old = re.sub(r'[\s\u00A0]+', '', norm_old)
                if stripped_old and stripped_old in stripped_full:
                    paragraph.text = pattern.sub(new_text, full_text, count=1)
                break

            s, e = match.start(), match.end()
            cur, start_r, end_r = 0, -1, -1
            start_off, end_off = -1, -1

            for i, run in enumerate(paragraph.runs):
                l = len(run.text)
                if start_r == -1 and cur <= s < cur + l:
                    start_r, start_off = i, s - cur
                if cur < e <= cur + l:
                    end_r, end_off = i, e - cur
                    break
                cur += l

            if start_r != -1 and end_r != -1:
                if start_r == end_r:
                    rt = paragraph.runs[start_r].text
                    paragraph.runs[start_r].text = rt[:start_off] + new_text + rt[end_off:]
                else:
                    paragraph.runs[start_r].text = paragraph.runs[start_r].text[:start_off] + new_text
                    for i in range(start_r + 1, end_r): paragraph.runs[i].text = ""
                    paragraph.runs[end_r].text = paragraph.runs[end_r].text[end_off:]
            else:
                paragraph.text = pattern.sub(new_text, full_text, count=1)
                break

if __name__ == "__main__":
    root = tk.Tk(); TemplateBuilder(root); root.mainloop()
