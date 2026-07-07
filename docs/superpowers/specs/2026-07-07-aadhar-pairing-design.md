# Specification: Aadhaar Image Pairing & Dynamic Tab Renaming

This specification outlines the client-side design and implementation for grouping/pairing front and back Aadhaar card images and dynamically renaming preview tabs based on manual party role assignments in RM-Maker.

## 1. Problem Description

Currently, when verifying extracted KYC data:
1. **No Pairing**: Aadhaar cards uploaded as separate front and back image files are treated as independent files. The user must manually click between separate tabs (e.g. `Aadhar_front.jpg` and `Aadhar_back.jpg`) to verify info (e.g., matching the name on the front and the address on the back).
2. **Generic Filenames**: Uploaded documents retain their original filenames in the tab list (e.g. `12345.jpg`), making it difficult to remember which file belongs to which borrower, bank signer, or witness.

---

## 2. Proposed Changes

We will implement the entire solution client-side in [case.html](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/web_templates/case.html) for simplicity, performance, and to avoid changing the verified backend schema.

### A. Aadhaar Front/Back Pair Detection
We will implement a client-side pairing algorithm `findPairedFile(filename, allFiles)`:
1. Clean the base name (lowercase, strip non-alphanumeric characters).
2. Check for keywords `front` / `f` / `obverse` / `1` for the front side, and `back` / `b` / `reverse` / `2` for the back side.
3. If one of these is found, swap it to search for the paired file in the list.
4. If no keywords are found, fallback to sorting alphabetically (first file is Front, second file is Back).

### B. Tabbed Quick-Toggle Interface (Option C)
When a file is loaded in the preview frame:
1. If the file has a paired image detected, the preview header will render two floating buttons: `[Front]` and `[Back]`.
2. These buttons allow the user to toggle instantly between the front and back images inside the preview frame without finding the other tab in the sidebar.

### C. Dynamic Tab Renaming
We will implement `updateFileTabLabels()` which scans:
1. Currently filled party fields in the DOM (Borrowers `bs`, Witnesses `ws`, Bank Signer `bsign`, Sellers `sellers`, Buyers `buyers`).
2. Matches these names or the last 4 digits of Aadhaar IDs against the uploaded filenames using fuzzy matching.
3. Rewrites the text content of the horizontal file preview tabs and the sidebar file list elements:
   * *Aadhaar Front:* `📄 Borrower 1 (Kiran Devi) - Aadhaar [Front]`
   * *Aadhaar Back:* `📄 Borrower 1 (Kiran Devi) - Aadhaar [Back]`
4. This function will run on page load and instantly on click of the **Apply Assignments** button.

---

## 3. Verification Plan

### Manual Verification
1. Open a case with multiple uploaded front/back Aadhaar images.
2. Select a tab (e.g., `aadhar_front.jpg`). Verify that floating `[Front]` and `[Back]` buttons appear in the preview frame, and clicking `[Back]` loads the back image immediately.
3. Assign the Aadhaar card to a borrower (e.g., "Kiran Devi") in the unassigned Aadhaar table and click "Apply Assignments".
4. Verify that the tabs and file lists are instantly renamed to `Borrower 1 (Kiran Devi) - Aadhaar [Front]` and `Borrower 1 (Kiran Devi) - Aadhaar [Back]`.
5. Refresh the page and verify that the renamed tabs persist on load.
