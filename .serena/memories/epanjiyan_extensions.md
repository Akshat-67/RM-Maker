# e-Panjiyan Extensions Memory

The e-Panjiyan extension suite automates the transfer of verified case session data directly into Rajasthan's official e-Panjiyan property registration portal.

## Modules
1. **Registered Mortgage (RM) Autofill**: Located in [epanjiyan_autofill](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/extensions/epanjiyan_autofill).
2. **Sale Deed (SD) Autofill**: Located in [epanjiyan_sd_autofill](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/extensions/epanjiyan_sd_autofill).

## Component Architecture
- **`manifest.json`**: Configures permissions, background scripts, and host permissions for `127.0.0.1` (to communicate with the local Flask server) and `epanjiyan.nic.in`.
- **`popup.html`/`popup.js`**: Reads local case files from Flask `/api/cases` endpoint and allows operators to select and load the active case.
- **`content.js`**: Injected script that queries the DOM, populates form elements, manipulates `Select2` dropdown elements, handles datepickers, and programmatically executes clicks.

## Key Automation Steps
- **District/SRO Selection**: Auto-navigates district modals.
- **Self Category Selection (Urban/Rural)**: Matches case gender distributions to e-Panjiyan category values:
  - Male-only: General Male (1)
  - Female-only: General Female (3)
  - Joint Male/Female: Male/Female Joint (6)
- **Face Value calculation**: Sums up loan amounts for RM or inputs the total sale value for SD.
- **Form Navigation**: Fills and clicks "Save" or "Calculate Duty", bypassing verification modals.
