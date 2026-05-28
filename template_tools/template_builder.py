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
        self.root.title("LegalDoc Master Template Creator v5")
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
        ]
        self.setup_ui()

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

    def update_checklist_status(self):
        all_mapped_tags = " ".join(self.mapping.values())
        for label, tag, var, cb in self.checklist_items:
            found = tag in all_mapped_tags; var.set(found); cb.config(fg=self.c_success if found else self.c_danger)

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
            doc = Document(self.doc_path); content = self.get_doc_content(doc)
            prompt = f"Identify variable fields and map to tags: rd, ad, bs[i].(s,n,a,r,rn,adr,id), ls[i].(n,a,w,t), ps[i].(adr,n,s,e,w), bsign.(n,r,rn), ws[i].(n,r,rn,adr). Return ONLY JSON dictionary {{'Exact Doc Text': '{{{{tag}}}}'}}. Text:\n{content}"
            extractor = DataExtractor(self.api_key_entry.get())
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
        if save_p: doc.save(save_p); messagebox.showinfo("Done", "Template generated!")

    def safe_replace(self, p, old, new):
        if not old or old == new: return
        match = self.find_fuzzy_match(p, old)
        if match:
            s_r, s_o, e_r, e_o = match
            if s_r == e_r: p.runs[s_r].text = p.runs[s_r].text[:s_o] + new + p.runs[s_r].text[e_o:]
            else:
                p.runs[s_r].text = p.runs[s_r].text[:s_o] + new
                for i in range(s_r + 1, e_r): p.runs[i].text = ""
                p.runs[e_r].text = p.runs[e_r].text[e_o:]

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
