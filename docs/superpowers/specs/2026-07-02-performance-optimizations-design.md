# Spec: RM-Maker Performance Optimizations Design

## 1. SQLite Database Session Storage

### Objective
Replace JSON file-based database scaling $O(N)$ with SQLite database accessed via SQLAlchemy.

### Database Schema (`models/case.py`)
```python
from flask_sqlalchemy import SQLAlchemy
import time

db = SQLAlchemy()

class Case(db.Model):
    __tablename__ = 'cases'
    
    id = db.Column(db.String(100), primary_key=True)  # case_id
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
    
    # JSON arrays stored as text/JSON columns
    verified_fields = db.Column(db.Text, nullable=True)     # JSON string of list
    processed_files = db.Column(db.Text, nullable=True)     # JSON string of list
    files = db.Column(db.Text, nullable=True)               # JSON string of list
    legal_report_files = db.Column(db.Text, nullable=True)  # JSON string of list
    
    # Case core data dictionary (fully converted to english digits)
    data = db.Column(db.Text, nullable=True)                # JSON string
    
    last_updated = db.Column(db.Float, default=time.time, onupdate=time.time)
```

### Integration in `app.py`
1. Initialize Flask-SQLAlchemy pointing to `sqlite:///cases/cases.db`.
2. Rewrite `load_case_session` and `save_case_session` to query and update `Case` table.
3. Keep method signatures identical. Serialize/deserialize JSON lists and dicts.
4. Rewrite `list_cases()` to run single DB query fetching only metadata fields.

### Migration Script (`scripts/migrate_sessions.py`)
Scan `cases/case_*/session.json`. Load contents. Insert into SQLite table `cases`. Preserve existing timestamps.

---

## 2. Gemini PDF Pre-filtering

### Objective
Reduce API token overhead and prompt latency by pre-filtering searchable PDFs.

### RM PDF Filtering (`modules/rm/extractor.py`)
1. Implement `_filter_relevant_pages(pages_text)` scoring pages based on keywords:
   - Priority 1 (Score 3): `loan`, `sanction`, `mortgage`, `borrower`, `guarantor`, `interest rate`, `property`.
   - Priority 2 (Score 1): `aadhaar`, `pan`, `co-applicant`, `schedule`.
2. Extract text with `pypdf`. If searchable, filter top-scoring pages. Compile as text prompt payload.
3. If scanned, fallback to sending entire PDF binary.

### SD PDF Filtering (`modules/sd/extractor.py`)
In `SDDataExtractor.extract_buckets_with_ai`, apply existing `_filter_relevant_pages` on `buckets["legal"]` documents if text is extractable. Avoid sending raw binary payloads for searchable legal reports.
