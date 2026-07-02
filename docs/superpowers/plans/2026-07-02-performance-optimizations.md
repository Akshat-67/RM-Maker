# Performance Optimizations Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate session storage to SQLite DB and implement Gemini PDF page pre-filtering.

**Architecture:** Use Flask-SQLAlchemy with single `cases` table holding case metadata and data JSON blob. Use `pypdf` text extraction and keyword relevance scoring to filter searchable PDF pages sent to Gemini API.

**Tech Stack:** Python 3.14+, SQLite, SQLAlchemy, Flask-SQLAlchemy, pypdf, pytest.

## Global Constraints
- Do NOT modify the core extraction prompt, merging logic, relation splitting, or normalization helper functions in `modules/sd/extractor.py`, `modules/rm/extractor.py`, `modules/rm/schema.py`, or `utils/helpers.py` without consent.
- Maintain universal English digit conversion.
- Do NOT change DevLys conversion logic.
- Keep compatibility with existing API formats.

---

### Task 1: Create Database Model

**Files:**
- Create: `models/case.py`
- Test: `tests/test_db_model.py`

**Interfaces:**
- Produces: `Case` class model mapping DB table `cases`.

- [ ] **Step 1: Write test to verify Case model creation**
```python
# tests/test_db_model.py
import pytest
import time
from models.case import Case, db
from flask import Flask

@pytest.fixture
def app():
    app = Flask("test_app")
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    with app.app_context():
        db.create_all()
        yield app

def test_case_model(app):
    with app.app_context():
        case = Case(
            id="test_case_1",
            doc_type="RM",
            property_type="Plot",
            data='{"key": "value"}',
            last_updated=time.time()
        )
        db.session.add(case)
        db.session.commit()
        
        fetched = Case.query.get("test_case_1")
        assert fetched is not None
        assert fetched.doc_type == "RM"
        assert fetched.data == '{"key": "value"}'
```

- [ ] **Step 2: Run test to verify it fails**
Run: `python -m pytest tests/test_db_model.py`
Expected: Fail (ModuleNotFoundError: No module named 'models')

- [ ] **Step 3: Implement Case model**
```python
# models/case.py
from flask_sqlalchemy import SQLAlchemy
import time

db = SQLAlchemy()

class Case(db.Model):
    __tablename__ = 'cases'
    
    id = db.Column(db.String(100), primary_key=True)
    doc_type = db.Column(db.String(10), default="RM")
    bank = db.Column(db.String(100), nullable=True)
    borrower_count = db.Column(db.Integer, default=1)
    loan_count = db.Column(db.Integer, default=1)
    properties_count = db.Column(db.Integer, default=1)
    sellers_count = db.Column(db.Integer, default=1)
    buyers_count = db.Column(db.Integer, default=1)
    chain_scenario = db.Column(db.String(100), nullable=True)
    selected_template = db.Column(db.String(255), nullable=True)
    property_type = db.Column(db.String(50), default="Plot")
    
    verified_fields = db.Column(db.Text, nullable=True)
    processed_files = db.Column(db.Text, nullable=True)
    files = db.Column(db.Text, nullable=True)
    legal_report_files = db.Column(db.Text, nullable=True)
    
    data = db.Column(db.Text, nullable=True)
    last_updated = db.Column(db.Float, default=time.time, onupdate=time.time)
```

- [ ] **Step 4: Run test to verify it passes**
Run: `python -m pytest tests/test_db_model.py`
Expected: Pass

- [ ] **Step 5: Commit**
```bash
git add models/case.py tests/test_db_model.py
git commit -m "feat: add case database model"
```

---

### Task 2: Create Migration Script

**Files:**
- Create: `scripts/migrate_sessions.py`
- Test: `tests/test_migration.py`

**Interfaces:**
- Produces: `migrate_json_to_sqlite(cases_dir, db_uri)`

- [ ] **Step 1: Write test verifying migration logic**
```python
# tests/test_migration.py
import os
import json
import tempfile
from models.case import Case, db
from scripts.migrate_sessions import migrate_json_to_sqlite
from flask import Flask

def test_migration():
    temp_dir = tempfile.mkdtemp()
    case_dir = os.path.join(temp_dir, "case_test123")
    os.makedirs(case_dir)
    
    session_data = {
        "id": "case_test123",
        "doc_type": "SD",
        "bank": "ICICI",
        "borrower_count": "2",
        "loan_count": "1",
        "properties_count": "1",
        "sellers_count": "1",
        "buyers_count": "1",
        "chain_scenario": "ScenarioA",
        "selected_template": "template.docx",
        "property_type": "Flat",
        "verified_fields": ["field1"],
        "processed_files": ["file1.pdf"],
        "files": ["file1.pdf"],
        "legal_report_files": ["report.pdf"],
        "data": {"name": "Test Customer"},
        "last_updated": 123456789.0
    }
    
    with open(os.path.join(case_dir, "session.json"), "w") as f:
        json.dump(session_data, f)
        
    app = Flask("test_migrate_app")
    db_path = os.path.join(temp_dir, "test.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
        
    migrate_json_to_sqlite(temp_dir, f"sqlite:///{db_path}")
    
    with app.app_context():
        case = Case.query.get("case_test123")
        assert case is not None
        assert case.doc_type == "SD"
        assert case.bank == "ICICI"
        assert json.loads(case.data) == {"name": "Test Customer"}
        assert case.last_updated == 123456789.0
```

- [ ] **Step 2: Run test to verify it fails**
Run: `python -m pytest tests/test_migration.py`
Expected: Fail (ModuleNotFoundError)

- [ ] **Step 3: Implement migration script**
```python
# scripts/migrate_sessions.py
import os
import json
from flask import Flask
from models.case import Case, db

def migrate_json_to_sqlite(cases_dir, db_uri):
    app = Flask("migration_app")
    app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
        
        if not os.path.exists(cases_dir):
            return
            
        for d in os.listdir(cases_dir):
            path = os.path.join(cases_dir, d, "session.json")
            if not os.path.exists(path):
                continue
                
            try:
                with open(path, "r", encoding="utf-8") as f:
                    sess = json.load(f)
                
                case_id = sess.get("id") or d
                if not case_id:
                    continue
                    
                # Skip duplicate
                if Case.query.get(case_id):
                    continue
                
                case = Case(
                    id=case_id,
                    doc_type=sess.get("doc_type", "RM"),
                    bank=sess.get("bank"),
                    borrower_count=int(sess.get("borrower_count")) if str(sess.get("borrower_count", "")).isdigit() else 1,
                    loan_count=int(sess.get("loan_count")) if str(sess.get("loan_count", "")).isdigit() else 1,
                    properties_count=int(sess.get("properties_count")) if str(sess.get("properties_count", "")).isdigit() else 1,
                    sellers_count=int(sess.get("sellers_count")) if str(sess.get("sellers_count", "")).isdigit() else 1,
                    buyers_count=int(sess.get("buyers_count")) if str(sess.get("buyers_count", "")).isdigit() else 1,
                    chain_scenario=sess.get("chain_scenario"),
                    selected_template=sess.get("selected_template"),
                    property_type=sess.get("property_type", "Plot"),
                    verified_fields=json.dumps(sess.get("verified_fields", [])),
                    processed_files=json.dumps(sess.get("processed_files", [])),
                    files=json.dumps(sess.get("files", [])),
                    legal_report_files=json.dumps(sess.get("legal_report_files", [])),
                    data=json.dumps(sess.get("data", {})),
                    last_updated=float(sess.get("last_updated", 0.0))
                )
                db.session.add(case)
            except Exception as e:
                print(f"Error migrating {path}: {e}")
                
        db.session.commit()

if __name__ == "__main__":
    migrate_json_to_sqlite("cases", "sqlite:///cases/cases.db")
```

- [ ] **Step 4: Run test to verify it passes**
Run: `python -m pytest tests/test_migration.py`
Expected: Pass

- [ ] **Step 5: Run migration on actual data**
Run: `python scripts/migrate_sessions.py`
Expected: Execution finishes without errors.

- [ ] **Step 6: Commit**
```bash
git add scripts/migrate_sessions.py tests/test_migration.py
git commit -m "feat: add migration script"
```

---

### Task 3: Integrate DB in App Routes

**Files:**
- Modify: `app.py`
- Test: Run pytest tests/

**Interfaces:**
- Consumes: `Case` table in SQLite DB
- Produces: SQLite-backed routing for all case APIs.

- [ ] **Step 1: Setup SQLAlchemy config in `app.py`**
Modify `app.py` near top imports:
```python
from models.case import Case, db
import json
```
Setup DB connection path configuration:
```python
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///cases/cases.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

with app.app_context():
    db.create_all()
```

- [ ] **Step 2: Rewrite `load_case_session` to read from DB**
Modify `app.py:179-252` to query SQLite DB instead of `session.json` file:
```python
def load_case_session(case_id):
    case_id = sanitize_case_id(case_id)
    case = Case.query.get(case_id)
    if not case:
        return None
        
    # Reconstruct the expected session dict structure
    sess = {
        "id": case.id,
        "doc_type": case.doc_type,
        "bank": case.bank,
        "borrower_count": str(case.borrower_count),
        "loan_count": str(case.loan_count),
        "properties_count": str(case.properties_count),
        "sellers_count": str(case.sellers_count),
        "buyers_count": str(case.buyers_count),
        "chain_scenario": case.chain_scenario,
        "selected_template": case.selected_template,
        "property_type": case.property_type,
        "verified_fields": json.loads(case.verified_fields or "[]"),
        "processed_files": json.loads(case.processed_files or "[]"),
        "files": json.loads(case.files or "[]"),
        "legal_report_files": json.loads(case.legal_report_files or "[]"),
        "data": json.loads(case.data or "{}"),
        "last_updated": case.last_updated
    }
    
    # Auto-correct doc_type
    if sess.get("doc_type") == "RM":
        sel_temp = sess.get("selected_template", "")
        if "SD-" in sel_temp or "sale_deed" in sel_temp.lower():
            sess["doc_type"] = "SD"
            
    if "data" in sess:
        sess["data"] = convert_hindi_digits_to_english(sess["data"])
        if isinstance(sess["data"], dict):
            property_type = sess.get("property_type", "Plot")
            sess["data"]["property_type"] = property_type
            
            # Universal bidirectional synchronization
            for key_list_name in ["title_chain", "chain"]:
                chain_list = sess["data"].get(key_list_name, [])
                sync_template_keys_to_property_type(chain_list, property_type)
                for evt in chain_list:
                    if isinstance(evt, dict):
                        if "executant_name" in evt and not evt.get("s"):
                            evt["s"] = evt["executant_name"]
                        if "claimant_name" in evt and not evt.get("b"):
                            evt["b"] = evt["claimant_name"]
                        if "date" in evt and not evt.get("d"):
                            evt["d"] = evt["date"]
                        if "reg_book" in evt and not evt.get("b_no"):
                            evt["b_no"] = evt["reg_book"]
                        if "reg_vol" in evt and not evt.get("v_no"):
                            evt["v_no"] = evt["reg_vol"]
                        if "reg_page" in evt and not evt.get("p_no"):
                            evt["p_no"] = evt["reg_page"]
                        if "reg_no" in evt and not evt.get("r_no"):
                            evt["r_no"] = evt["reg_no"]
                        if "reg_add_book" in evt and not evt.get("add_book"):
                            evt["add_book"] = evt["reg_add_book"]
                        if "reg_add_vol" in evt and not evt.get("add_vol"):
                            evt["add_vol"] = evt["reg_add_vol"]
                        if "reg_add_page" in evt and not evt.get("add_page"):
                            evt["add_page"] = evt["reg_add_page"]
                            
                        # Reverse sync
                        if evt.get("s") and not evt.get("executant_name"):
                            evt["executant_name"] = evt["s"]
                        if evt.get("b") and not evt.get("claimant_name"):
                            evt["claimant_name"] = evt["b"]
                        if evt.get("d") and not evt.get("date"):
                            evt["date"] = evt.get("d")
                        if evt.get("b_no") and not evt.get("reg_book"):
                            evt["reg_book"] = evt["b_no"]
                        if evt.get("v_no") and not evt.get("reg_vol"):
                            evt["reg_vol"] = evt["v_no"]
                        if evt.get("p_no") and not evt.get("reg_page"):
                            evt["reg_page"] = evt["p_no"]
                        if evt.get("r_no") and not evt.get("reg_no"):
                            evt["reg_no"] = evt["r_no"]
            
            for p in sess["data"].get("ps", []):
                if isinstance(p, dict):
                    if "land_area" in p and not p.get("area"):
                        p["area"] = p["land_area"]
                    if "unit" in p and not p.get("area_unit"):
                        p["area_unit"] = p["unit"]
                    # Reverse sync
                    if p.get("area") and not p.get("land_area"):
                        p["land_area"] = p["area"]
                    if p.get("area_unit") and not p.get("unit"):
                        p["unit"] = p["area_unit"]
    return sess
```

- [ ] **Step 3: Rewrite `save_case_session` to write to DB**
Modify `app.py:262-300`:
```python
def save_case_session(case_id, data, files, verified_fields, bank, borrower_count, loan_count, properties_count="1", processed_files=None, doc_type=None, sellers_count=None, buyers_count=None, chain_scenario=None, selected_template=None, property_type=None, legal_report_files=None, buckets=None):
    case_id = sanitize_case_id(case_id)
    
    # Load existing first to merge fields
    existing = load_case_session(case_id) or {}
    
    if doc_type is None: doc_type = existing.get("doc_type", "RM")
    if sellers_count is None: sellers_count = existing.get("sellers_count", "1")
    if buyers_count is None: buyers_count = existing.get("buyers_count", "1")
    if chain_scenario is None: chain_scenario = existing.get("chain_scenario", "")
    if selected_template is None: selected_template = existing.get("selected_template", "")
    if property_type is None: property_type = existing.get("property_type", "Plot")
    if processed_files is None: processed_files = existing.get("processed_files", [])
    if legal_report_files is None: legal_report_files = existing.get("legal_report_files", [])
    
    # Merge logic
    existing_data = existing.get("data", {})
    merged_data = data.copy()
    
    if "unassigned_aadhars" in existing_data and "unassigned_aadhars" not in merged_data:
        merged_data["unassigned_aadhars"] = existing_data["unassigned_aadhars"]
        
    for key in ["ps", "sellers", "buyers", "ss", "bs", "ws", "chain", "title_chain"]:
        if key in existing_data and key in merged_data:
            existing_list = existing_data[key]
            incoming_list = merged_data[key]
            
            if isinstance(existing_list, list) and isinstance(incoming_list, list):
                merged_list = []
                for idx, incoming_item in enumerate(incoming_list):
                    if idx < len(existing_list):
                        existing_item = existing_list[idx]
                        if isinstance(existing_item, dict) and isinstance(incoming_item, dict):
                            merged_item = existing_item.copy()
                            merged_item.update(incoming_item)
                            merged_list.append(merged_item)
                    else:
                        merged_list.append(incoming_item)
                merged_data[key] = merged_list
                
    case = Case.query.get(case_id)
    if not case:
        case = Case(id=case_id)
        db.session.add(case)
        
    case.doc_type = doc_type
    case.bank = bank
    case.borrower_count = int(borrower_count) if str(borrower_count).isdigit() else 1
    case.loan_count = int(loan_count) if str(loan_count).isdigit() else 1
    case.properties_count = int(properties_count) if str(properties_count).isdigit() else 1
    case.sellers_count = int(sellers_count) if str(sellers_count).isdigit() else 1
    case.buyers_count = int(buyers_count) if str(buyers_count).isdigit() else 1
    case.chain_scenario = chain_scenario
    case.selected_template = selected_template
    case.property_type = property_type
    
    case.verified_fields = json.dumps(list(verified_fields))
    case.processed_files = json.dumps(processed_files)
    case.files = json.dumps(files)
    case.legal_report_files = json.dumps(legal_report_files)
    case.data = json.dumps(merged_data)
    case.last_updated = time.time()
    
    db.session.commit()
```

- [ ] **Step 4: Rewrite `list_cases` to fetch metadata only**
Modify `app.py:154-162`:
```python
def list_cases():
    cases_db = Case.query.order_by(Case.last_updated.desc()).all()
    cases = []
    for case in cases_db:
        cases.append({
            "id": case.id,
            "doc_type": case.doc_type,
            "bank": case.bank,
            "borrower_count": str(case.borrower_count),
            "loan_count": str(case.loan_count),
            "properties_count": str(case.properties_count),
            "sellers_count": str(case.sellers_count),
            "buyers_count": str(case.buyers_count),
            "chain_scenario": case.chain_scenario,
            "selected_template": case.selected_template,
            "property_type": case.property_type,
            "verified_fields": json.loads(case.verified_fields or "[]"),
            "processed_files": json.loads(case.processed_files or "[]"),
            "files": json.loads(case.files or "[]"),
            "legal_report_files": json.loads(case.legal_report_files or "[]"),
            "data": json.loads(case.data or "{}"),
            "last_updated": case.last_updated
        })
    return cases
```

- [ ] **Step 5: Run test suite to verify everything works**
Run: `python -m pytest tests/`
Expected: Pass

- [ ] **Step 6: Commit**
```bash
git add app.py
git commit -m "feat: integrate database session storage into app.py"
```

---

### Task 4: RM PDF Pre-filtering

**Files:**
- Modify: `modules/rm/extractor.py`
- Test: `tests/test_rm_prefiltering.py`

**Interfaces:**
- Produces: `RMDataExtractor._filter_relevant_pages(pages_text)`
- Modify: `RMDataExtractor.extract_with_ai` (handles PDF parsing and filtering)

- [ ] **Step 1: Write test for RM PDF prefiltering**
```python
# tests/test_rm_prefiltering.py
from modules.rm.extractor import RMDataExtractor

def test_rm_prefiltering_scores():
    extractor = RMDataExtractor(api_keys=[])
    pages = [
        (1, "This page talks about loan agreement, mortgage, borrower details, and interest rate"),
        (2, "This page has random filler text about history and other non-relevant information"),
        (3, "Guarantor property details list and schedule items original")
    ]
    texts, nums = extractor._filter_relevant_pages(pages, min_pages_threshold=1, score_threshold=1)
    assert 1 in nums
    assert 3 in nums
    assert 2 not in nums
```

- [ ] **Step 2: Run test to verify it fails**
Run: `python -m pytest tests/test_rm_prefiltering.py`
Expected: Fail (AttributeError: 'RMDataExtractor' object has no attribute '_filter_relevant_pages')

- [ ] **Step 3: Implement `_filter_relevant_pages` and integrate into `extract_with_ai`**
Modify `modules/rm/extractor.py:95-120`:
```python
    def _filter_relevant_pages(self, pages_text, min_pages_threshold=8, score_threshold=2):
        """Pre-filters pages of text-searchable PDFs based on high-relevance title flow keywords."""
        total_pages = len(pages_text)
        if total_pages <= min_pages_threshold:
            return [text for _, text in pages_text], list(range(1, total_pages + 1))

        primary_keywords = [
            "loan", "sanction", "mortgage", "borrower", "guarantor", "interest rate", 
            "property", "sanction letter", "mortgage deed", "loan amount", "rate of interest"
        ]
        secondary_keywords = [
            "aadhaar", "pan", "co-applicant", "schedule", "address", "signatory", "witness"
        ]

        page_scores = []
        total_extracted_len = 0
        for page_num, text in pages_text:
            total_extracted_len += len(text)
            score = 0
            text_lower = text.lower()
            
            for kw in primary_keywords:
                if kw in text_lower:
                    score += 3
            for kw in secondary_keywords:
                if kw in text_lower:
                    score += 1
            page_scores.append((page_num, score, text))

        if total_extracted_len < 200:
            return None, None

        selected_indices = set()
        for idx, (page_num, score, _) in enumerate(page_scores):
            if score >= score_threshold:
                selected_indices.add(idx)
                if idx + 1 < total_pages: selected_indices.add(idx + 1)
                if idx - 1 >= 0: selected_indices.add(idx - 1)

        selected_indices = sorted(list(selected_indices))
        if not selected_indices:
            return [text for _, text in pages_text], list(range(1, total_pages + 1))

        selected_texts = [page_scores[i][2] for i in selected_indices]
        selected_page_nums = [page_scores[i][0] for i in selected_indices]
        return selected_texts, selected_page_nums

    def extract_with_ai(self, file_paths, selected_model, bank_name="", expected_borrowers=None,
                        expected_loans=None, expected_witnesses=2, borrower_hints="", witness_hints="",
                        current_data=None, **kwargs):
        """Extract data from files using Google Gemini API with PDF page pre-filtering."""
        if not self.api_keys:
            return {"error": "Gemini API Keys Missing"}

        contents = []
        for path in file_paths:
            ext = os.path.splitext(path)[1].lower()
            mime_type, _ = mimetypes.guess_type(path)
            if ext == '.pdf':
                try:
                    import pypdf
                    pages_text = []
                    reader = pypdf.PdfReader(path)
                    for idx, page in enumerate(reader.pages):
                        text = page.extract_text() or ""
                        pages_text.append((idx + 1, text))
                    
                    selected_texts, selected_pages = self._filter_relevant_pages(pages_text)
                    if selected_texts is not None:
                        combined_filtered_text = f"--- PDF Page-Filtered Content ({os.path.basename(path)}) ---\n"
                        for p_num, p_text in zip(selected_pages, selected_texts):
                            combined_filtered_text += f"\n--- PAGE {p_num} ---\n{p_text}\n"
                        contents.append(types.Part.from_text(text=combined_filtered_text))
                        print(f"[Pre-filter] Successfully filtered {os.path.basename(path)} to pages {selected_pages}")
                        continue
                except Exception as pdf_err:
                    print(f"[Pre-filter Warning] Failed to pre-filter PDF {path}: {pdf_err}")

                with open(path, 'rb') as f:
                    raw = f.read()
                contents.append(types.Part.from_bytes(data=raw, mime_type=mime_type or 'application/octet-stream'))
            elif ext in ['.jpg', '.jpeg', '.png']:
                with open(path, 'rb') as f:
                    raw = f.read()
                contents.append(types.Part.from_bytes(data=raw, mime_type=mime_type or 'application/octet-stream'))
            elif ext == '.txt':
                with open(path, 'r', encoding='utf-8') as f:
                    contents.append(types.Part.from_text(text=f.read()))
```

- [ ] **Step 4: Run test to verify it passes**
Run: `python -m pytest tests/test_rm_prefiltering.py`
Expected: Pass

- [ ] **Step 5: Commit**
```bash
git add modules/rm/extractor.py tests/test_rm_prefiltering.py
git commit -m "feat: implement PDF pre-filtering in RM extractor"
```

---

### Task 5: SD Legal Bucket Pre-filtering

**Files:**
- Modify: `modules/sd/extractor.py`
- Test: `tests/test_sd_legal_prefiltering.py`

**Interfaces:**
- Modify: `SDDataExtractor.extract_buckets_with_ai` (applies pre-filtering to `buckets["legal"]`)

- [ ] **Step 1: Write integration test for SD legal bucket prefiltering**
```python
# tests/test_sd_legal_prefiltering.py
import os
import tempfile
from modules.sd.extractor import SDDataExtractor

def test_sd_legal_prefiltering_runs():
    extractor = SDDataExtractor(api_keys=["dummy_key"])
    # We mock _call_gemini to just return dummy data instead of hitting actual API
    extractor._call_gemini = lambda model, contents, prompt: {"ps": [{"adr": "Mock Address"}]}
    
    # Create a dummy searchable PDF
    from reportlab.pdfgen import canvas
    temp_dir = tempfile.mkdtemp()
    pdf_path = os.path.join(temp_dir, "legal_report.pdf")
    c = canvas.Canvas(pdf_path)
    c.drawString(100, 750, "This page talks about chain of title, विक्रय पत्र, and deeds.")
    c.save()
    
    buckets = {"legal": [pdf_path]}
    result = extractor.extract_buckets_with_ai(buckets, "gemini-2.5-flash")
    assert result is not None
```

- [ ] **Step 2: Run test to verify it fails**
Run: `python -m pytest tests/test_sd_legal_prefiltering.py`
Expected: Fail (ImportError: No module named 'reportlab.pdfgen')
*(If reportlab is missing, add `reportlab` to requirements.txt and run pip install, or use pypdf directly to generate dummy PDF. Let's make the test generate a dummy pdf using reportlab if installed or write a helper)*. Let's install `reportlab` or use a pre-existing PDF from test files. We can also just mock `pypdf.PdfReader`.

- [ ] **Step 3: Modify `modules/sd/extractor.py`**
In `SDDataExtractor.extract_buckets_with_ai`, update the integration of `buckets["legal"]`:
```python
        # 2. Legal - Extract Property and Chain only (Primary Source)
        if buckets.get("legal"):
            legal_prompt = self._build_legal_prompt()
            # Apply PDF prefiltering to legal report
            legal_files = buckets["legal"]
            filtered_contents = []
            for path in legal_files:
                ext = os.path.splitext(path)[1].lower()
                if ext == '.pdf':
                    try:
                        import pypdf
                        pages_text = []
                        reader = pypdf.PdfReader(path)
                        for idx, page in enumerate(reader.pages):
                            text = page.extract_text() or ""
                            pages_text.append((idx + 1, text))
                        
                        selected_texts, selected_pages = self._filter_relevant_pages(pages_text)
                        if selected_texts is not None:
                            combined_filtered_text = f"--- Legal Report Page-Filtered Content ({os.path.basename(path)}) ---\n"
                            for p_num, p_text in zip(selected_pages, selected_texts):
                                combined_filtered_text += f"\n--- PAGE {p_num} ---\n{p_text}\n"
                            from google.genai import types
                            filtered_contents.append(types.Part.from_text(text=combined_filtered_text))
                            print(f"[Pre-filter] Successfully filtered legal report {os.path.basename(path)} to pages {selected_pages}")
                            continue
                    except Exception as pdf_err:
                        print(f"[Pre-filter Warning] Failed to pre-filter legal report PDF {path}: {pdf_err}")
                
                # Fallback to default raw file extraction logic
                import mimetypes
                from google.genai import types
                mime_type, _ = mimetypes.guess_type(path)
                if ext in ['.jpg', '.jpeg', '.png', '.pdf']:
                    with open(path, 'rb') as f:
                        raw = f.read()
                    filtered_contents.append(types.Part.from_bytes(data=raw, mime_type=mime_type or 'application/octet-stream'))
                elif ext == '.txt':
                    with open(path, 'r', encoding='utf-8') as f:
                        filtered_contents.append(types.Part.from_text(text=f.read()))

            legal_res = self._call_gemini(selected_model, filtered_contents, legal_prompt)
            if legal_res and not legal_res.get("error"):
                merged_data = self._merge_legal_results(merged_data, legal_res, file_paths=buckets["legal"])
```

- [ ] **Step 4: Run test to verify it passes**
Run: `python -m pytest tests/test_sd_legal_prefiltering.py`
Expected: Pass

- [ ] **Step 5: Commit**
```bash
git add modules/sd/extractor.py tests/test_sd_legal_prefiltering.py
git commit -m "feat: implement PDF pre-filtering on SD legal bucket extraction"
```
