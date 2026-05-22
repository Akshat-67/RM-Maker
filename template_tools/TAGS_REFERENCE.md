# Short-Form Tagging System (v2)

To prevent breaking layout in tight Word documents, use these shortened tags.

### 1. General Info
- `{{rd}}`: RM Date
- `{{ad}}`: Loan Agreement Date

### 2. Borrowers (Loop: `{% for b in bs %}`)
- `{{b.s}}`: Salutation (Mr/Mrs)
- `{{b.n}}`: Name
- `{{b.a}}`: Age
- `{{b.r}}`: Relation (S/o, W/o)
- `{{b.rn}}`: Relative's Name
- `{{b.adr}}`: Address
`{% endfor %}`

### 3. Loans (Loop: `{% for l in ls %}`)
- `{{l.n}}`: LAN Number
- `{{l.a}}`: Amount (figures)
- `{{l.w}}`: Amount (words)
`{% endfor %}`

### 4. Property (Loop: `{% for p in ps %}`)
- `{{p.adr}}`: Full Address
- `{{p.n}}`: North
- `{{p.s}}`: South
- `{{p.e}}`: East
- `{{p.w}}`: West
`{% endfor %}`

### 5. Bank Signatory
- `{{bsign.n}}`: Name
- `{{bsign.r}}`: Relation (e.g., S/o)
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
