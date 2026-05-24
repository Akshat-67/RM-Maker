# Short-Form Tagging System (v2.1)

### 1. General Info
- `{{rd}}`: RM Date
- `{{ad}}`: Loan Agreement Date

### 2. Borrowers (Loop: `{% for b in bs %}`)
- `{{b.s}}`: Salutation
- `{{b.n}}`: Name
- `{{b.a}}`: Age
- `{{b.r}}`: Relation
- `{{b.rn}}`: Relative's Name
- `{{b.adr}}`: Address
- `{{b.id}}`: Aadhar/ID Number
`{% endfor %}`

### 3. Loans (Loop: `{% for l in ls %}`)
- `{{l.n}}`: LAN Number
- `{{l.a}}`: Amount (figures)
- `{{l.w}}`: Amount (words)
- `{{l.t}}`: Tenure (e.g., 180 Months)
`{% endfor %}`

### 4. Property (Loop: `{% for p in ps %}`)
- `{{p.adr}}`: Full Address/Description
- `{{p.n}}`: North
- `{{p.s}}`: South
- `{{p.e}}`: East
- `{{p.w}}`: West
`{% endfor %}`

### 5. Bank Signatory
- `{{bsign.n}}`: Name
- `{{bsign.r}}`: Relation
- `{{bsign.rn}}`: Relative Name

### 6. Witnesses (Loop: `{% for w in ws %}`)
- `{{w.n}}`: Name
- `{{w.r}}`: Relation
- `{{w.rn}}`: Relative Name
- `{{w.adr}}`: Address
`{% endfor %}`

### 7. Documents (Loop: `{% for d in ds %}`)
- `{{d.t}}`: Document text
`{% endfor %}`
