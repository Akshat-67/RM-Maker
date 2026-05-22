import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
from extractor import DataExtractor
from processor import TemplateProcessor

class LawApp:
    def __init__(self, root):
        self.root = root
        self.root.title("LegalDoc Automator - RM Generator")
        self.root.geometry("800x600")

        self.files = []
        self.template_path = ""
        self.extracted_data = {}

        self.setup_ui()

    def setup_ui(self):
        # File Selection Frame
        frame = tk.LabelFrame(self.root, text="Step 1: Select OCR Files & Template", padx=10, pady=10)
        frame.pack(fill="x", padx=10, pady=5)

        tk.Button(frame, text="Add OCR Text Files", command=self.add_ocr_files).grid(row=0, column=0, pady=5)
        self.file_list = tk.Listbox(frame, height=4)
        self.file_list.grid(row=0, column=1, padx=10, sticky="ew")

        tk.Button(frame, text="Select Word Template", command=self.select_template).grid(row=1, column=0, pady=5)
        self.template_label = tk.Label(frame, text="No template selected", fg="blue")
        self.template_label.grid(row=1, column=1, sticky="w")

        # API Key Frame
        api_frame = tk.Frame(frame)
        api_frame.grid(row=2, column=0, columnspan=2, sticky="w", pady=5)
        tk.Label(api_frame, text="Gemini API Key:").pack(side="left")
        self.api_key_entry = tk.Entry(api_frame, width=40, show="*")
        self.api_key_entry.pack(side="left", padx=5)

        # Action Frame
        action_frame = tk.Frame(self.root)
        action_frame.pack(pady=10)
        tk.Button(action_frame, text="Extract Data", command=self.run_extraction, bg="green", fg="white", font=("Arial", 12, "bold")).pack()

        # Data Verification Frame (Scrollable)
        self.verify_frame = tk.LabelFrame(self.root, text="Step 2: Verify & Edit Data", padx=10, pady=10)
        self.verify_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.canvas = tk.Canvas(self.verify_frame)
        self.scrollbar = ttk.Scrollbar(self.verify_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

    def add_ocr_files(self):
        paths = filedialog.askopenfilenames(filetypes=[("Text files", "*.txt")])
        for p in paths:
            if p not in self.files:
                self.files.append(p)
                self.file_list.insert(tk.END, os.path.basename(p))

    def select_template(self):
        path = filedialog.askopenfilename(filetypes=[("Word documents", "*.docx")])
        if path:
            self.template_path = path
            self.template_label.config(text=os.path.basename(path))

    def run_extraction(self):
        if not self.files or not self.template_path:
            messagebox.showerror("Error", "Please select OCR files and a template.")
            return

        api_key = self.api_key_entry.get()
        if not api_key:
            messagebox.showwarning("Warning", "No API Key provided. Only basic extraction will work.")

        all_text = ""
        for f in self.files:
            with open(f, 'r', encoding='utf-8') as file:
                all_text += file.read() + "\n\n"

        extractor = DataExtractor(api_key if api_key else None)
        # Use AI for extraction
        self.extracted_data = extractor.extract_with_ai(all_text)

        self.display_data_for_verification()

    def display_data_for_verification(self):
        # Clear previous fields
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        if "error" in self.extracted_data:
            messagebox.showerror("AI Error", self.extracted_data["error"])
            return

        self.entries = {}

        # Display Borrowers
        tk.Label(self.scrollable_frame, text="BORROWERS", font=("Arial", 10, "bold")).pack(anchor="w")
        for i, b in enumerate(self.extracted_data.get('Borrowers', [])):
            f = tk.Frame(self.scrollable_frame, bd=1, relief="sunken", pady=5)
            f.pack(fill="x", pady=2)
            self.create_field(f, f"B{i+1} Name", b.get('name', ''), f"borrower_{i+1}_name")
            self.create_field(f, f"B{i+1} Age", b.get('age', ''), f"borrower_{i+1}_age")
            self.create_field(f, f"B{i+1} Relation", b.get('father_or_husband_name', ''), f"borrower_{i+1}_relation")
            self.create_field(f, f"B{i+1} Address", b.get('address', ''), f"borrower_{i+1}_address")

        # Loan Details
        tk.Label(self.scrollable_frame, text="LOAN DETAILS", font=("Arial", 10, "bold"), pady=10).pack(anchor="w")
        loan = self.extracted_data.get('Loan Details', {})
        self.create_field(self.scrollable_frame, "Loan Acc No", loan.get('loan_account_no', ''), "loan_acc_no")
        self.create_field(self.scrollable_frame, "Amount", loan.get('loan_amount', ''), "loan_amount")
        self.create_field(self.scrollable_frame, "Sanction Date", loan.get('sanction_date', ''), "sanction_date")

        # Documents
        tk.Label(self.scrollable_frame, text="DOCUMENTS (SECOND SCHEDULE)", font=("Arial", 10, "bold"), pady=10).pack(anchor="w")
        docs = self.extracted_data.get('Documents List', [])
        doc_text = "\n".join(docs) if isinstance(docs, list) else docs
        txt = tk.Text(self.scrollable_frame, height=10)
        txt.insert("1.0", doc_text)
        txt.pack(fill="x")
        self.entries["documents_list"] = txt

        tk.Button(self.scrollable_frame, text="Generate Final RM Document", command=self.generate_doc, bg="blue", fg="white").pack(pady=20)

    def create_field(self, parent, label, value, key):
        frame = tk.Frame(parent)
        frame.pack(fill="x")
        tk.Label(frame, text=label, width=15, anchor="w").pack(side="left")
        ent = tk.Entry(frame)
        ent.insert(0, str(value))
        ent.pack(side="left", fill="x", expand=True)
        self.entries[key] = ent

    def generate_doc(self):
        final_context = {}
        for key, widget in self.entries.items():
            if isinstance(widget, tk.Entry):
                final_context[key] = widget.get()
            elif isinstance(widget, tk.Text):
                # Split documents by newline for the template if needed
                docs = widget.get("1.0", tk.END).strip().split('\n')
                final_context[key] = [{"text": d} for d in docs if d.strip()]

        # Add amount in words
        extractor = DataExtractor()
        final_context['loan_amount_words'] = extractor.amount_to_words(final_context.get('loan_amount', '0'))

        save_path = filedialog.asksaveasfilename(defaultextension=".docx", filetypes=[("Word document", "*.docx")])
        if save_path:
            processor = TemplateProcessor(self.template_path)
            processor.generate(final_context, save_path)
            messagebox.showinfo("Success", f"Document generated at {save_path}")

if __name__ == "__main__":
    root = tk.Tk()
    app = LawApp(root)
    root.mainloop()
