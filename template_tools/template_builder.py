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
            ("Borrower 2 Relation", "{{bs[1].r}}"),
            ("Borrower 2 Rel Name", "{{bs[1].rn}}"),
            ("Borrower 2 Address", "{{bs[1].adr}}"),
            ("Borrower 2 Aadhar/ID", "{{bs[1].id}}"),
            ("Borrower 3 Salutation", "{{bs[2].s}}"),
            ("Borrower 3 Name", "{{bs[2].n}}"),
            ("Borrower 3 Relation", "{{bs[2].r}}"),
            ("Borrower 3 Rel Name", "{{bs[2].rn}}"),
            ("Borrower 3 Address", "{{bs[2].adr}}"),
            ("Borrower 3 Aadhar/ID", "{{bs[2].id}}"),
            ("Loan 1 LAN No", "{{ls[0].n}}"),
            ("Loan 1 Amount (Value)", "{{ls[0].a}}"),
            ("Loan 1 Amount (Words)", "{{ls[0].w}}"),
            ("Loan 1 Tenure", "{{ls[0].t}}"),
            ("Loan 2 LAN No", "{{ls[1].n}}"),
            ("Loan 2 Amount (Value)", "{{ls[1].a}}"),
            ("Loan 2 Amount (Words)", "{{ls[1].w}}"),
            ("Loan 2 Tenure", "{{ls[1].t}}"),
            ("Loan 3 LAN No", "{{ls[2].n}}"),
            ("Loan 3 Amount (Value)", "{{ls[2].a}}"),
            ("Loan 3 Amount (Words)", "{{ls[2].w}}"),
            ("Loan 3 Tenure", "{{ls[2].t}}"),
            ("Property 1 Address", "{{ps[0].adr}}"),
            ("Property 1 North", "{{ps[0].n}}"),
            ("Property 1 South", "{{ps[0].s}}"),
            ("Property 1 East", "{{ps[0].e}}"),
            ("Property 1 West", "{{ps[0].w}}"),
            ("Property 2 Address", "{{ps[1].adr}}"),
            ("Property 2 North", "{{ps[1].n}}"),
            ("Property 2 South", "{{ps[1].s}}"),
            ("Property 2 East", "{{ps[1].e}}"),
            ("Property 2 West", "{{ps[1].w}}"),
            ("Bank Signatory Name", "{{bsign.n}}"),
            ("Bank Signatory Rel", "{{bsign.r}}"),
            ("Bank Signatory Rel Name", "{{bsign.rn}}"),
            ("Witness 1 Name", "{{ws[0].n}}"),
            ("Witness 1 Relation", "{{ws[0].r}}"),
            ("Witness 1 Rel Name", "{{ws[0].rn}}"),
            ("Witness 1 Address", "{{ws[0].adr}}"),
            ("Witness 2 Name", "{{ws[1].n}}"),
            ("Witness 2 Relation", "{{ws[1].r}}"),
            ("Witness 2 Rel Name", "{{ws[1].rn}}"),
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
        self.discover_btn = tk.Button(left_panel, text="🔍 START FULL AI DATA DISCOVERY", command=self.discover_data, bg=self.c_success, fg="white", font=("Segoe UI", 13, "bold"), bd=0, pady=18, cursor="hand2")
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
        r1 = tk.LabelFrame(right_panel, text=" SMART GAP FIXER ", bg=self.c_panel, font=("Segoe UI", 10, "bold"), padx=15, pady=15, fg=self.c_danger)
        r1.pack(fill="x", pady=(0, 10))
        tk.Label(r1, text="Untick items on the left then run:", bg=self.c_panel, font=("Segoe UI", 9), justify="left", fg=self.c_text).pack(pady=5)
        self.refetch_btn = tk.Button(r1, text="REFETCH UNCHECKED FIELDS", command=self.refetch_missing, bg=self.c_danger, fg="white", font=("Segoe UI", 10, "bold"), bd=0, pady=15, cursor="hand2")
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
        if p:
            if not p.lower().endswith(".docx"):
                messagebox.showwarning("Unsupported Format", "Please select a .docx file. Older .doc files must be saved as .docx first.")
                return
            self.doc_path = p
            self.path_lbl.config(text=os.path.basename(p), fg=self.c_blue)

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

            MAPPING RULES:
            1. MINIMAL VALUE MAPPING (MANDATORY): Return the smallest exact variable text, not the static legal wording around it.
               GOOD: {{"24th day of March 2024": "{{{{rd}}}}"}}
               GOOD: {{"17,15,000": "{{{{ls[0].a}}}}"}}
               GOOD: {{"180 Months": "{{{{ls[0].t}}}}"}}
               BAD: {{"this 24th day of March 2024": "this {{{{rd}}}}"}}
               BAD: {{"MORTGAGE MONEY RS. 17,15,000/-": "MORTGAGE MONEY RS. {{{{ls[0].a}}}}/-"}}

            2. EXACT MATCH: The JSON key must be copied EXACTLY as it appears in the document text, including line breaks where shown.
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
               {{"Mr.": "{{{{bs[0].s}}}}", "Ram Kumar": "{{{{bs[0].n}}}}", "S/o": "{{{{bs[0].r}}}}", "Shyam Lal": "{{{{bs[0].rn}}}}", "Jaipur": "{{{{bs[0].adr}}}}"}}
               Exception: if a tiny value like "Mr." or "S/o" appears more than once, include the adjacent name to make it unique:
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
                self.mapping.update(self.suggest_common_mappings(content, self.mapping))
                self.root.after(0, self.update_tree)
            else: self.root.after(0, lambda: messagebox.showerror("AI Error", "AI failed to generate a valid mapping structure."))
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda msg=error_msg: messagebox.showerror("System Error", msg))
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
            Use MINIMAL VALUE MAPPING: return the exact variable value only, not surrounding static wording.
            Also look for ANY other names, dates, or unique numbers that haven't been tagged yet.
            Pay special attention to witness addresses, property address/schedule, salutations, relation markers (S/o/W/o/D/o), relative names, and loan tenure.

            SCHEMA: {self.expected_fields}

            TEXT:
            {content}

            Return ONLY a JSON dictionary: {{"EXACT TEXT": "TEXT WITH {{{{tags}}}}"}}
            """

            extractor = DataExtractor(self.api_key_entry.get())
            raw = extractor.raw_generate(prompt, self.model_var.get())
            if not raw:
                self.root.after(0, lambda: messagebox.showerror("AI Error", "AI returned an empty response."))
                return
            match = re.search(r'\{.*\}', raw, re.DOTALL)
            if match:
                new_data = self.clean_mapping(json.loads(match.group(0)))
                new_data.update(self.suggest_common_mappings(content, {**self.mapping, **new_data}))
                self.mapping.update(new_data)
                self.root.after(0, self.update_tree)
                self.root.after(0, lambda: messagebox.showinfo("Gap Fix Success", f"Added {len(new_data)} more entries! Check the checklist."))
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda msg=error_msg: messagebox.showerror("AI Error", msg))
        finally: self.root.after(0, lambda: self.refetch_btn.config(state="normal", text="REFETCH UNCHECKED FIELDS"))

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

    def tag_exists(self, mapping, tag):
        return tag in " ".join(str(v) for v in mapping.values())

    def suggest_common_mappings(self, content, mapping):
        suggestions = {}
        existing = {**mapping}

        for old, tag in list(mapping.items()):
            match = re.search(r"\{\{(bs|ws)\[(\d+)\]\.n\}\}", tag)
            if not match:
                continue

            group, index = match.group(1), match.group(2)
            prefix = f"{{{{{group}[{index}]."
            name = re.escape(old.strip())

            sal_tag = f"{prefix}s}}}}"
            name_tag = f"{prefix}n}}}}"
            if group == "bs" and not self.tag_exists(existing, sal_tag):
                sal_match = re.search(rf"\b(Mr\.|Mrs\.|Ms\.|Shri|Smt\.)\s+({name})\b", content, re.IGNORECASE)
                if sal_match:
                    phrase = sal_match.group(0)
                    replacement = f"{sal_tag} {name_tag}"
                    suggestions[phrase] = replacement
                    existing[phrase] = replacement

        for old, tag in list(mapping.items()):
            match = re.search(r"\{\{(bs|ws|bsign)\[?(\d*)\]?\.rn\}\}|\{\{bsign\.rn\}\}", tag)
            if not match:
                continue

            if "bsign" in tag:
                rel_tag = "{{bsign.r}}"
            else:
                group = "bs" if "{{bs[" in tag else "ws"
                index_match = re.search(r"\[(\d+)\]", tag)
                if not index_match:
                    continue
                rel_tag = f"{{{{{group}[{index_match.group(1)}].r}}}}"

            if self.tag_exists(existing, rel_tag):
                continue

            rel_name = re.escape(old.strip())
            rel_match = re.search(rf"\b(S/o|W/o|D/o|Son of|Wife of|Daughter of)\s+({rel_name})\b", content, re.IGNORECASE)
            if rel_match:
                phrase = rel_match.group(0)
                replacement = f"{rel_tag} {tag}"
                suggestions[phrase] = replacement
                existing[phrase] = replacement

        tenure_matches = []
        for tenure in re.findall(r"\b(?:60|84|96|120|144|180|240|300|360)\s*Months?\b", content, re.IGNORECASE):
            normalized = re.sub(r"\s+", " ", tenure).strip()
            if normalized not in tenure_matches:
                tenure_matches.append(normalized)

        unique_tenures = [t for t in tenure_matches if tenure_matches.count(t) == 1]
        for idx, tenure in enumerate(unique_tenures[:3]):
            tag = f"{{{{ls[{idx}].t}}}}"
            if not self.tag_exists(existing, tag):
                suggestions[tenure] = tag
                existing[tenure] = tag

        return self.clean_mapping(suggestions)

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
        reps = sorted(self.clean_mapping(self.mapping).items(), key=lambda x: len(x[0]), reverse=True)

        for _, part in self.iter_story_parts(doc):
            for p in self.iter_paragraphs_deep(part):
                self.apply_reps(p, reps)

        save_p = filedialog.asksaveasfilename(defaultextension=".docx", initialfile="MASTER_TEMPLATE_READY.docx")
        if save_p:
            doc.save(save_p)
            messagebox.showinfo("Complete", "Master Template Generated with 100% original styles preserved!")

    def apply_reps(self, p, reps):
        if not p.text.strip(): return
        for old, new in reps:
            self.safe_replace_text_preserving_format(p, old, new)

    def safe_replace_text_preserving_format(self, paragraph, old_text, new_text):
        """Replace without assigning paragraph.text, because that destroys Word run formatting."""
        if not old_text or old_text == new_text: return

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

    def replace_text_preserving_format(self, paragraph, old_text, new_text):
        """Indestructible replacement engine: Preserves styles even if Word splits text into weird runs."""
        return self.safe_replace_text_preserving_format(paragraph, old_text, new_text)
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
                    return self.safe_replace_text_preserving_format(paragraph, old_text, new_text)
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
                return self.safe_replace_text_preserving_format(paragraph, old_text, new_text)
                break

if __name__ == "__main__":
    root = tk.Tk(); TemplateBuilder(root); root.mainloop()
