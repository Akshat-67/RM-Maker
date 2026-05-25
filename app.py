import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import threading
import re
import zipfile
from extractor import DataExtractor
from processor import TemplateProcessor

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD  # type: ignore
except (ImportError, ModuleNotFoundError):
    DND_FILES = None
    TkinterDnD = None

# --- DESIGN CONSTANTS (MODERN PROFESSIONAL ENTERPRISE) ---
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
DEFAULT_GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or "AIzaSyDs32YIJx35FDhb9qOa3vTcWDtU-RpL5_w"

class LawApp:
    def __init__(self, root):
        self.root = root
        self.root.title("LegalDoc Automator Pro - RM Generator v4")
        self.root.geometry("1400x980")
        self.root.configure(bg=BG_MAIN)
        self.files = []
        self.extracted_data = {}
        self.template_map = {}
        self.custom_template_path = tk.StringVar(value="")
        self.discover_templates()
        self.setup_ui()

    def discover_templates(self):
        """Automatically scan the templates/ directory to build the template map."""
        self.template_map = {}
        if not os.path.exists("templates"):
            return

        files = []
        for root_dir, _, names in os.walk("templates"):
            parent = os.path.basename(root_dir)
            if parent and parent.lower() != "templates":
                self.template_map.setdefault(parent.upper(), {"Single": {}, "Multiple": {}})
            for name in names:
                if name.lower().endswith(".docx"):
                    files.append(os.path.join(root_dir, name))

        for path in files:
            if not self.docx_has_placeholders(path):
                continue
            # Expected format: BANK_BORR_LOAN.docx (e.g., ICICI_SINGLE_1.docx)
            # Or use a more flexible heuristic if needed
            f = os.path.basename(path)
            parent = os.path.basename(os.path.dirname(path))
            name = os.path.splitext(f)[0]
            parts = name.split("_")
            if len(parts) >= 3 or parent.upper() not in {"", "TEMPLATES"}:
                bank = parent.upper() if parent.upper() not in {"", "TEMPLATES"} else parts[0].upper()
                borr = "Single" if "SINGLE" in f.upper() else "Multiple"
                # Extract loan count
                loan_match = re.search(r'(\d+)', f)
                loan_key = f"{loan_match.group(1)} Loan" if loan_match else "1 Loan"
                if loan_match and int(loan_match.group(1)) >= 3:
                    loan_key = "3+ Loans"
                elif loan_match and int(loan_match.group(1)) == 2:
                    loan_key = "2 Loans"

                if bank not in self.template_map: self.template_map[bank] = {"Single": {}, "Multiple": {}}
                self.template_map[bank][borr][loan_key] = path

        # Fallbacks for banks found but missing specific combinations
        for bank in self.template_map:
            for borr in ["Single", "Multiple"]:
                keys = list(self.template_map[bank][borr].keys())
                if not keys: continue
                # If "1 Loan" missing, use first available
                if "1 Loan" not in self.template_map[bank][borr]:
                    self.template_map[bank][borr]["1 Loan"] = self.template_map[bank][borr][keys[0]]
                if "2 Loans" not in self.template_map[bank][borr]:
                    self.template_map[bank][borr]["2 Loans"] = self.template_map[bank][borr][keys[0]]
                if "3+ Loans" not in self.template_map[bank][borr]:
                    self.template_map[bank][borr]["3+ Loans"] = self.template_map[bank][borr][keys[0]]

    def docx_has_placeholders(self, path):
        try:
            with zipfile.ZipFile(path) as zf:
                for name in zf.namelist():
                    if name.startswith("word/") and name.endswith(".xml"):
                        if "{{" in zf.read(name).decode("utf-8", errors="ignore"):
                            return True
        except Exception:
            return False
        return False

    def setup_ui(self):
        # MAIN CONTAINER: Header
        header = tk.Frame(self.root, bg=PRIMARY_NAV, height=70)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)
        tk.Label(header, text="LegalDoc Automator Pro", bg=PRIMARY_NAV, fg="white", font=("Segoe UI", 18, "bold"), padx=30).pack(side="left")
        tk.Label(header, text="RM GENERATION ENGINE v4.1", bg=PRIMARY_NAV, fg="#94A3B8", font=("Segoe UI", 9, "bold"), padx=30).pack(side="right")

        # MAIN BODY: Split View
        main_body = tk.Frame(self.root, bg=BG_MAIN)
        main_body.pack(fill="both", expand=True)

        # LEFT PANEL: Configuration
        self.left_p_container = tk.Frame(main_body, bg=SURFACE_CARD, width=400, bd=0, highlightthickness=1, highlightbackground=BORDER_COLOR)
        self.left_p_container.pack(side="left", fill="y", padx=(20, 10), pady=20)
        self.left_p_container.pack_propagate(False)

        canvas_l = tk.Canvas(self.left_p_container, bg=SURFACE_CARD, highlightthickness=0)
        scroll_l = ttk.Scrollbar(self.left_p_container, orient="vertical", command=canvas_l.yview)
        self.left_p = tk.Frame(canvas_l, bg=SURFACE_CARD, padx=20)
        self.left_p.bind("<Configure>", lambda e: canvas_l.configure(scrollregion=canvas_l.bbox("all")))
        canvas_l.create_window((0, 0), window=self.left_p, anchor="nw", width=360)
        canvas_l.configure(yscrollcommand=scroll_l.set)
        canvas_l.pack(side="left", fill="both", expand=True)
        scroll_l.pack(side="right", fill="y")

        # RIGHT PANEL: Verification
        self.right_p_container = tk.Frame(main_body, bg=BG_MAIN)
        self.right_p_container.pack(side="left", fill="both", expand=True, padx=(10, 20), pady=0)

        self.setup_left_panel()
        self.setup_right_panel()

    def create_section_title(self, parent, text):
        f = tk.Frame(parent, bg=SURFACE_CARD)
        f.pack(fill="x", pady=(25, 12))
        tk.Label(f, text=text, bg=SURFACE_CARD, fg=PRIMARY_NAV, font=FONT_DISPLAY, anchor="w").pack(side="left")
        tk.Frame(f, bg=BORDER_COLOR, height=1).pack(side="left", fill="x", expand=True, padx=(15, 0))

    def create_card(self, parent, title=None, is_danger=False):
        card = tk.Frame(parent, bg=SURFACE_CARD, bd=0, highlightthickness=1,
                        highlightbackground=BTN_DANGER if is_danger else BORDER_COLOR)
        card.pack(fill="x", pady=10)
        inner = tk.Frame(card, bg=SURFACE_CARD, padx=18, pady=18)
        inner.pack(fill="both", expand=True)
        if title:
            header_f = tk.Frame(inner, bg=SURFACE_CARD)
            header_f.pack(fill="x", pady=(0, 15))
            tk.Label(header_f, text=title, bg=SURFACE_CARD, fg=TEXT_SECONDARY, font=FONT_HEADER, anchor="w").pack(side="left")
        return inner
