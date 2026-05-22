import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import threading
from extractor import DataExtractor
from processor import TemplateProcessor

class LawApp:
    def __init__(self, root):
        self.root = root
        self.root.title("LegalDoc Automator - RM Generator")
        self.root.geometry("900x700")

        self.files = []
        self.template_path = ""
        self.extracted_data = {}

        self.setup_ui()

    def setup_ui(self):
        # File Selection Frame
        frame = tk.LabelFrame(self.root, text="Step 1: Select Input Documents & Template", padx=10, pady=10)
        frame.pack(fill="x", padx=10, pady=5)

        file_btn_frame = tk.Frame(frame)
        file_btn_frame.grid(row=0, column=0, sticky="n")

        tk.Button(file_btn_frame, text="Add Files (Images/PDF/Text)", command=self.add_files, width=25).pack(pady=2)
        tk.Button(file_btn_frame, text="Clear Selected Files", command=self.clear_files, width=25).pack(pady=2)

        self.file_list = tk.Listbox(frame, height=6, width=60)
        self.file_list.grid(row=0, column=1, padx=10, sticky="ew")

        tk.Button(frame, text="Select Word Template", command=self.select_template, width=25).grid(row=1, column=0, pady=5)
        self.template_label = tk.Label(frame, text="No template selected", fg="blue")
        self.template_label.grid(row=1, column=1, sticky="w")

        # API Key Frame
        api_frame = tk.Frame(frame)
        api_frame.grid(row=2, column=0, columnspan=2, sticky="w", pady=5)
        tk.Label(api_frame, text="Gemini API Key:").pack(side="left")
        self.api_key_entry = tk.Entry(api_frame, width=50, show="*")
        self.api_key_entry.pack(side="left", padx=5)

        # Action Frame
        self.action_frame = tk.Frame(self.root)
        self.action_frame.pack(pady=10)

        self.extract_btn = tk.Button(self.action_frame, text="Extract Data (AI)", command=self.start_extraction_thread,
                                     bg="#4CAF50", fg="white", font=("Arial", 12, "bold"), width=20)
        self.extract_btn.pack()

        self.status_label = tk.Label(self.root, text="Ready", fg="grey")
        self.status_label.pack()

        # Data Verification Frame
        self.verify_frame = tk.LabelFrame(self.root, text="Step 2: Verify & Edit Extracted Data", padx=10, pady=10)
        self.verify_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.canvas = tk.Canvas(self.verify_frame)
        self.scrollbar = ttk.Scrollbar(self.verify_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Make canvas width follow frame width
        self.root.bind("<Configure>", self.on_frame_configure)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

    def on_frame_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width - 40)

    def add_files(self):
        paths = filedialog.askopenfilenames(filetypes=[
            ("All supported", "*.jpg *.jpeg *.png *.pdf *.txt"),
            ("Images", "*.jpg *.jpeg *.png"),
            ("PDF files", "*.pdf"),
            ("Text files", "*.txt")
        ])
        for p in paths:
            if p not in self.files:
                self.files.append(p)
                self.file_list.insert(tk.END, f"[{os.path.splitext(p)[1][1:].upper()}] {os.path.basename(p)}")

    def clear_files(self):
        self.files = []
        self.file_list.delete(0, tk.END)

    def select_template(self):
        path = filedialog.askopenfilename(filetypes=[("Word documents", "*.docx")])
        if path:
            self.template_path = path
            self.template_label.config(text=os.path.basename(path))

    def start_extraction_thread(self):
        if not self.files or not self.template_path:
            messagebox.showerror("Error", "Please select input files and a template.")
            return

        api_key = self.api_key_entry.get()
        if not api_key:
            messagebox.showerror("Error", "Please enter a Gemini API Key.")
            return

        self.extract_btn.config(state="disabled", text="Processing...")
        self.status_label.config(text="AI is analyzing documents, please wait...", fg="orange")

        # Run extraction in a separate thread to keep UI responsive
        thread = threading.Thread(target=self.run_extraction, args=(api_key,))
        thread.start()

    def run_extraction(self, api_key):
        try:
            extractor = DataExtractor(api_key)
            self.extracted_data = extractor.extract_with_ai(self.files)

            # Update UI from the main thread
            self.root.after(0, self.display_data_for_verification)
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("System Error", str(e)))
        finally:
            self.root.after(0, self.reset_ui_state)

    def reset_ui_state(self):
        self.extract_btn.config(state="normal", text="Extract Data (AI)")
        self.status_label.config(text="Processing complete", fg="green")

    def display_data_for_verification(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        if "error" in self.extracted_data:
            messagebox.showerror("AI Error", self.extracted_data["error"])
            return

        self.entries = {}

        # Borrowers Section
        tk.Label(self.scrollable_frame, text="BORROWERS", font=("Arial", 11, "bold"), fg="#1976D2").pack(anchor="w", pady=(10, 5))
        borrowers = self.extracted_data.get('Borrowers', [])
        for i, b in enumerate(borrowers):
            f = tk.LabelFrame(self.scrollable_frame, text=f"Borrower {i+1}", padx=5, pady=5)
            f.pack(fill="x", pady=5)
            self.create_field(f, "Full Name", b.get('name', ''), f"borrower_{i+1}_name")
            self.create_field(f, "Age", b.get('age', ''), f"borrower_{i+1}_age")
            self.create_field(f, "S/O, W/O, D/O", b.get('father_or_husband_name', ''), f"borrower_{i+1}_relation")
            self.create_field(f, "Full Address", b.get('address', ''), f"borrower_{i+1}_address")

        # Loan Details Section
        tk.Label(self.scrollable_frame, text="LOAN DETAILS", font=("Arial", 11, "bold"), fg="#1976D2").pack(anchor="w", pady=(15, 5))
        loan = self.extracted_data.get('Loan Details', {})
        self.create_field(self.scrollable_frame, "Loan Acc No", loan.get('loan_account_no', ''), "loan_acc_no")
        self.create_field(self.scrollable_frame, "Loan Amount", loan.get('loan_amount', ''), "loan_amount")
        self.create_field(self.scrollable_frame, "Sanction Date", loan.get('sanction_date', ''), "sanction_date")
        self.create_field(self.scrollable_frame, "Tenure (Months)", loan.get('tenure_months', ''), "tenure")

        # Documents Section
        tk.Label(self.scrollable_frame, text="SECOND SCHEDULE (DOCUMENTS)", font=("Arial", 11, "bold"), fg="#1976D2").pack(anchor="w", pady=(15, 5))
        docs = self.extracted_data.get('Documents List', [])
        doc_text = "\n".join(docs) if isinstance(docs, list) else str(docs)

        txt_frame = tk.Frame(self.scrollable_frame)
        txt_frame.pack(fill="x")
        txt = tk.Text(txt_frame, height=12, font=("Consolas", 10))
        txt.insert("1.0", doc_text)
        txt.pack(fill="x")
        self.entries["documents_list"] = txt

        # Final Generate Button
        tk.Button(self.scrollable_frame, text="Generate Final Word Document", command=self.generate_doc,
                  bg="#2196F3", fg="white", font=("Arial", 12, "bold"), pady=10).pack(fill="x", pady=20)

    def create_field(self, parent, label, value, key):
        frame = tk.Frame(parent)
        frame.pack(fill="x", pady=2)
        tk.Label(frame, text=label, width=20, anchor="w").pack(side="left")
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
                docs = widget.get("1.0", tk.END).strip().split('\n')
                final_context[key] = [{"text": d.strip()} for d in docs if d.strip()]

        # Generate amount in words automatically
        extractor = DataExtractor()
        final_context['loan_amount_words'] = extractor.amount_to_words(final_context.get('loan_amount', '0'))

        save_path = filedialog.asksaveasfilename(defaultextension=".docx", filetypes=[("Word document", "*.docx")])
        if save_path:
            try:
                processor = TemplateProcessor(self.template_path)
                processor.generate(final_context, save_path)
                messagebox.showinfo("Success", f"Document generated successfully at:\n{save_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to generate document: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = LawApp(root)
    root.mainloop()
