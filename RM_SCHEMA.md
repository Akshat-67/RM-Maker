# Registered Mortgage (RM) Template Schema & Placeholders

This document lists all Registered Mortgage (RM) placeholders and fields processed by the RM template engine (`modules/rm/processor.py` and `modules/rm/extractor.py`) for rendering Word docx templates.

---

### 1. Borrowers / Buyers (`bs`)
List of borrowers associated with the mortgage.
* **Format**: `bs[i]` (e.g. `bs[0]`, `bs[1]`)
* **Available Fields**:
  * `bs[i].s`: Salutation prefix (e.g. `"Mr."`, `"Mrs."`, `"Ms"`)
  * `bs[i].n`: Full name of the borrower (e.g. `"VIVEK SAXENA"`)
  * `bs[i].a`: Age of the borrower (e.g. `"59"`)
  * `bs[i].dob`: Date of Birth (e.g. `"30/06/1967"`)
  * `bs[i].r`: Relation type prefix (e.g. `"S/o"`, `"W/o"`, `"D/o"`)
  * `bs[i].rn`: Name of relative (e.g. `"LATE J.B. SAXENA"`)
  * `bs[i].relation_text`: Combined relation string (e.g. `"S/o LATE J.B. SAXENA"`)
  * `bs[i].adr`: Residential Address (e.g. `"FLAT NO 101, 1ST FLOOR..."`)
  * `bs[i].id`: ID Proof / Aadhaar card digits (e.g. `"556409639476"`)
  * `bs[i].pan`: PAN Card Number (e.g. `"AKHPS7097L"`)

---

### 2. Bank Signatory (`bsign`)
Details of the bank officer signing the mortgage deed.
* **Format**: `bsign`
* **Available Fields**:
  * `bsign.s`: Salutation prefix (e.g. `"Mr."`, `"Mrs."`)
  * `bsign.n`: Full name of the signing officer (e.g. `"SURESH SHARMA"`)
  * `bsign.a`: Age of the signatory (e.g. `"42"`)
  * `bsign.dob`: Date of birth of the signatory (e.g. `"15/08/1984"`)
  * `bsign.d`: Designation (e.g. `"BRANCH MANAGER"`)
  * `bsign.r`: Relation type prefix (e.g. `"S/o"`)
  * `bsign.rn`: Relative's name (e.g. `"RAMESH SHARMA"`)
  * `bsign.relation_text`: Combined relation string (e.g. `"S/o RAMESH SHARMA"`)
  * `bsign.pan`: PAN Card number (e.g. `"ABCDE1234F"`)
  * `bsign.id`: ID Card/Aadhaar card digits (e.g. `"999988887777"`)
  * `bsign.adr`: Signatory office / residential address (e.g. `"ICICI BANK BRANCH, JAIPUR"`)

---

### 3. Properties (`ps`)
List of properties mortgaged under the deed.
* **Format**: `ps[i]`
* **Available Fields**:
  * `ps[i].adr`: Address of the property (e.g. `"PLOT NO 115-A, MUHANA..."`)
  * `ps[i].adr_en`: Address in English (e.g. `"PLOT NO 115-A, MUHANA..."`)
  * `ps[i].area`: Size of the property (e.g. `"120"`)
  * `ps[i].area_unit`: Area measurement unit (e.g. `"Sq. Yards"`)
  * `ps[i].n`: Boundary North (e.g. `"PLOT NO 10"`)
  * `ps[i].s`: Boundary South (e.g. `"ROAD 30 FT"`)
  * `ps[i].e`: Boundary East (e.g. `"PLOT NO 12"`)
  * `ps[i].w`: Boundary West (e.g. `"OTHER LAND"`)
  * `ps[i].lat`: Latitude coordinates (e.g. `"26.8524"`)
  * `ps[i].lng`: Longitude coordinates (e.g. `"75.7618"`)
  * `ps[i].lease_deed_no`: Registered Lease Deed/Sale Deed No. (e.g. `"12345"`)

---

### 4. Loans (`ls`)
List of loans associated with the mortgage.
* **Format**: `ls[i]`
* **Available Fields**:
  * `ls[i].n`: Bank / Branch name, or Loan Account Number (e.g. `"ICICI BANK LTD"`)
  * `ls[i].a`: Sanctioned Loan Amount in digits (e.g. `"4500000"`)
  * `ls[i].w`: Sanctioned Loan Amount in words (e.g. `"Forty Five Lakh Rupees Only"`)
  * `ls[i].t`: Tenure/Term of the loan (e.g. `"240 Months"`)
  * `ls[i].emi`: Monthly Installment (EMI) in digits (e.g. `"96013"`)
  * `ls[i].emi_w`: Monthly Installment in words (e.g. `"Ninety Six Thousand Thirteen"`)
  * `ls[i].r_rate`: Loan interest rate (e.g. `"12.00%"`)

---

### 5. Witnesses (`ws`)
Witnesses to the execution of the mortgage.
* **Format**: `ws[i]`
* **Available Fields**:
  * `ws[i].n`: Witness Full Name (e.g. `"PAWAN KUMAR"`)
  * `ws[i].a`: Age of the witness (e.g. `"30"`)
  * `ws[i].dob`: Date of birth of the witness (e.g. `"10/04/1996"`)
  * `ws[i].r`: Relation type prefix (e.g. `"S/o"`)
  * `ws[i].rn`: Relative's name (e.g. `"DAUDAYAL"`)
  * `ws[i].relation_text`: Combined relation text (e.g. `"S/o DAUDAYAL"`)
  * `ws[i].adr`: Resident Address (e.g. `"FLAT NO.LG-1 LOWER VINAYAK..."`)
  * `ws[i].id`: Aadhaar Card / ID number (e.g. `"373056203432"`)

---

### 6. Prior Documents / Title Chain (`ds`)
List of prior deeds/documents.
* **Format**: `ds[i]`
* **Available Fields**:
  * `ds[i].t`: Description of the prior title document (e.g. `"Lease Deed dated 12/05/2005..."`)

---

### 7. Global & Derived Parameters
* **`rd`**: Registry Date / execution date (e.g. `"06-07-2026"`)
* **`ad`**: Agreement Date / Loan Sanction Date (e.g. `"05-07-2026"`)
* **`ds_text` / `second_schedule` / `Chain_Text`**: Combined formatted title chain narrative representing the entire historical ownership of the property (often used to render the Second Schedule).
