# e-Panjiyan Chrome Extension Suite

This document describes the design, autofill state machine, timing optimizations, and selector structures of the Chrome extension suite for the e-Panjiyan portal.

---

## 1. Extension Directory & Files
The extension directories reside in `/extensions`:

- **[epanjiyan_autofill/](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/extensions/epanjiyan_autofill/)**: Handles automated feeding for Registered Mortgage (RM) cases.
- **[epanjiyan_sd_autofill/](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/extensions/epanjiyan_sd_autofill/)**: Handles automated feeding for Sale Deed (SD) cases.
- **`content.js`**: Orchestrates form element detection, input injection, and step progression.
- **`popup.html` / `popup.js`**: Fetch case sessions from the Flask server, list unimported files, and trigger the autofill sequence.

---

## 2. One-Click Autofill State Machine
The autofill flow uses a state machine tracked in browser `localStorage` (scoped by `case_id`) to automatically progress across multiple screens:

```
Popup: Trigger Autofill 
       ↓
State: Ingest Presenter Details
       ↓
State: Fill Party Details (Loop through: Borrower → Bank Officer → Witness 1 → Witness 2)
       ↓
State: Fill Property Details & Auto-Calculate Stamp Duty
       ↓
Complete Ingestion
```

1. **Presenter Details**: Detects form controls and fills in authorized presenter info.
2. **Party Details Loop**: Matches party roles, opens party modals, autofills details, handles verification popups, and clicks "OK" / "Save".
3. **Property Details**: Populates registry zone, colony name, plot numbers, dimensions, and calculates stamp duty.

---

## 3. Performance & Stability Rules
To guarantee fast execution and prevent rendering race conditions on the portal:
- **No Artificial Delays**: Avoid static `setTimeout` calls between input fields; use `Promise.all` to inject text inputs concurrently.
- **50ms Modal Polling**: Rather than waiting with static delays, use a rapid 50ms polling interval to check for SweetAlert popup confirmations and click them instantly.
- **Select2 Option Matching**: Portal dropdowns use Select2. To select values reliably, match option texts strictly and trigger `change` events to fire portal backend listeners.
- **Bilingual Fallbacks**: Search for options using English and Hindi bilingual labels (e.g. searching "Plot" and "भूखण्ड") to handle portal locale fluctuations.
- **Loop-Proofing**: Prevent routing loops by validating page URL coordinates and checking for the presence of destination navigation buttons before executing transitions.
