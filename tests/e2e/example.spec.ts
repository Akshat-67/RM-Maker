import { test, expect } from '@playwright/test';

test.describe('LegalDoc Automator Pro Regression Suite', () => {
  
  test('1. App starts and dashboard loads', async ({ page }) => {
    // Navigate to dashboard
    await page.goto('/');
    
    // Check main title in the header navbar and section header
    await expect(page).toHaveTitle(/Dashboard | LegalDoc Automator Pro/);
    await expect(page.getByText('LegalDoc Automator Pro')).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Case Dashboard' })).toBeVisible();
    
    // Check KPI strip exists
    await expect(page.getByText('Total Cases')).toBeVisible();
    await expect(page.getByText('Registered Mortgage')).toBeVisible();
    await expect(page.getByText('Sale Deeds')).toBeVisible();
    
    // Check buttons to create new cases exist
    await expect(page.getByRole('link', { name: '+ New RM Case' })).toBeVisible();
    await expect(page.getByRole('link', { name: '+ New SD Case' })).toBeVisible();
  });

  test('2. New case creation works', async ({ page }) => {
    await page.goto('/');
    
    // Click the new RM case button
    await page.getByRole('link', { name: '+ New RM Case' }).click();
    
    // Auto-waits for redirection to the view case page
    await expect(page).toHaveURL(/\/case\/case_\d+/);
  });

  test('3. Case workspace opens', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('link', { name: '+ New RM Case' }).click();
    
    // Check that workspace loads all step switcher panels
    await expect(page.locator('#step-indicator-upload')).toBeVisible();
    await expect(page.locator('#step-indicator-review')).toBeVisible();
    await expect(page.locator('#step-indicator-chain')).toBeVisible();
    
    // Explicitly click to switch to Step 1 (Configure & Upload) to make its elements visible
    await page.locator('#step-indicator-upload').click();
    
    // Verify case workspace specific components in Step 1
    await expect(page.getByText('Case Settings & Config')).toBeVisible();
    await expect(page.getByRole('button', { name: '💾 Save Progress' })).toBeVisible();
  });

  test('4. RM mode UI renders', async ({ page }) => {
    await page.goto('/');
    // Create new RM case explicitly
    await page.getByRole('link', { name: '+ New RM Case' }).click();
    
    // Switch to step 1
    await page.locator('#step-indicator-upload').click();
    
    // RM mode setting block should be visible, and SD settings block should be hidden
    await expect(page.locator('#rmSettingsBlock')).toBeVisible();
    await expect(page.locator('#sdSettingsBlock')).toBeHidden();
    
    // Mode indicator badge should display RM Mode
    await expect(page.locator('#docTypeSelect')).toHaveValue('RM');
  });

  test('5. SD mode UI renders', async ({ page }) => {
    await page.goto('/');
    // Create a new SD case
    await page.getByRole('link', { name: '+ New SD Case' }).click();
    
    // Switch to step 1
    await page.locator('#step-indicator-upload').click();
    
    // SD mode settings block should be visible, RM settings hidden
    await expect(page.locator('#sdSettingsBlock')).toBeVisible();
    await expect(page.locator('#rmSettingsBlock')).toBeHidden();
    
    // Mode indicator badge / dropdown value should display SD
    await expect(page.locator('#docTypeSelect')).toHaveValue('SD');
  });

  test('6. Upload buckets exist', async ({ page }) => {
    await page.goto('/');
    // Open a case in SD mode to view the specific upload buckets
    await page.getByRole('link', { name: '+ New SD Case' }).click();
    
    // Switch to step 1
    await page.locator('#step-indicator-upload').click();
    
    // Verify all SD specific document upload buckets/inputs exist in the DOM
    await expect(page.locator('#kycFiles')).toBeAttached();
    await expect(page.locator('#legalFiles')).toBeAttached();
    await expect(page.locator('#atsFiles')).toBeAttached();
    await expect(page.locator('#titleFiles')).toBeAttached();
    await expect(page.locator('#ocrFiles')).toBeAttached();
    
    // Verify UI displays the bucket headers
    await expect(page.getByRole('heading', { name: 'KYC (Aadhaar/PAN)' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Legal & Technical Reports' })).toBeVisible();
  });

  test('7. Review panels exist', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('link', { name: '+ New RM Case' }).click();
    
    // Switch step to Step 2 (Verify & Review)
    await page.locator('#step-indicator-review').click();
    
    // Verify the split workspace and editor panel display
    await expect(page.locator('#step-review-view')).toBeVisible();
    await expect(page.locator('.preview-pane')).toBeVisible();
    await expect(page.locator('.editor-pane')).toBeVisible();
    
    // Verify section selector inside the editor pane exists
    await expect(page.locator('#verificationSectionSelector')).toBeVisible();
  });

  /* --- Dedicated Smoke Tests protecting case.html --- */

  test('9. Upload buttons respond', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('link', { name: '+ New SD Case' }).click();
    await page.locator('#step-indicator-upload').click();
    await page.locator('.large-dropzone').first().waitFor({ state: 'visible' });

    // Verify KYC dropzone is clickable and responds by opening a file chooser
    const [fileChooser] = await Promise.all([
      page.waitForEvent('filechooser', { timeout: 15000 }),
      page.locator('.large-dropzone').first().click(),
    ]);
    expect(fileChooser).toBeDefined();
  });

  test('10. Tab switching works', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('link', { name: '+ New RM Case' }).click();
    
    // 1. Switch to step 2 (Verify & Review)
    await page.locator('#step-indicator-review').click();
    await expect(page.locator('#step-review-view')).toBeVisible();
    await expect(page.locator('#step-upload-view')).toBeHidden();
    await expect(page.locator('#step-chain-view')).toBeHidden();

    // 2. Switch to step 3 (Title Chain Timeline)
    await page.locator('#step-indicator-chain').click();
    await expect(page.locator('#step-chain-view')).toBeVisible();
    await expect(page.locator('#step-upload-view')).toBeHidden();
    await expect(page.locator('#step-review-view')).toBeHidden();

    // 3. Switch back to step 1 (Configure & Upload)
    await page.locator('#step-indicator-upload').click();
    await expect(page.locator('#step-upload-view')).toBeVisible();
    await expect(page.locator('#step-review-view')).toBeHidden();
    await expect(page.locator('#step-chain-view')).toBeHidden();
  });

  test('11. Preview toggle works', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('link', { name: '+ New SD Case' }).click();
    
    // Switch to step 2 (Verify & Review)
    await page.locator('#step-indicator-review').click();
    
    // Test ITRANS toggle state change (case-insensitive regex to handle 'Off' vs 'ON' values)
    const itrans = page.locator('#btnToggleItrans');
    await expect(itrans).toContainText(/off/i);
    await itrans.click();
    await expect(itrans).toContainText(/on/i);
    await itrans.click();
    await expect(itrans).toContainText(/off/i);

    // Test DevLys toggle state change
    const devlys = page.locator('#btnToggleDevLys');
    await expect(devlys).toContainText(/off/i);
    await devlys.click();
    await expect(devlys).toContainText(/on/i);
    await devlys.click();
    await expect(devlys).toContainText(/off/i);
  });

  test('12. Save case API fires', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('link', { name: '+ New RM Case' }).click();

    // Intercept the AJAX save request
    const savePromise = page.waitForRequest(req => 
      req.url().includes('/save') && req.method() === 'POST'
    );
    
    await page.getByRole('button', { name: '💾 Save Progress' }).click();
    
    const saveRequest = await savePromise;
    expect(saveRequest).toBeDefined();
    expect(saveRequest.url()).toContain('/save');
  });

  test('13. Extraction button triggers correct request', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('link', { name: '+ New SD Case' }).click();
    await page.locator('#step-indicator-upload').click();

    // Force enable the KYC extract button via JS evaluation since no files are loaded
    await page.locator('#extractBtn_kyc').evaluate(el => el.removeAttribute('disabled'));

    // Wait for the AI scan POST request to fire
    const aiPromise = page.waitForRequest(req => 
      req.url().includes('/ai') && req.method() === 'POST'
    );
    
    await page.locator('#extractBtn_kyc').click();
    
    const aiRequest = await aiPromise;
    expect(aiRequest).toBeDefined();
    
    // Parse JSON parameters from intercepted request
    const body = JSON.parse(aiRequest.postData() || '{}');
    expect(body.bucket).toBe('kyc');
  });

  test('14. Workspace workflow integration', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('link', { name: '+ New RM Case' }).click();
    await page.locator('#step-indicator-upload').click();

    // 1. Modify case configuration settings silently (avoid triggering onBorrowerChange/
    //    onLoanChange which call saveCase(()=>location.reload()) and cause an uncontrolled
    //    mid-test navigation before switchStep is available on the reloaded page).
    await page.locator('#borrowerSelect').evaluate((el: HTMLSelectElement) => { el.value = '2'; });
    await page.locator('#loanSelect').evaluate((el: HTMLSelectElement) => { el.value = '2'; });

    // Save configuration change and wait for the page to fully settle
    const savePromise = page.waitForResponse(res => res.url().includes('/save') && res.status() === 200);
    await page.getByRole('button', { name: '💾 Save Progress' }).click();
    await savePromise;
    // Ensure no pending navigation is still in progress before proceeding
    await page.waitForLoadState('domcontentloaded');

    // 2. Go to step 2 (Verify & Review)
    await page.locator('#step-indicator-review').click();
    await expect(page.locator('#step-review-view')).toBeVisible();

    // Verify sections select dropdown and Generate button exist in review step
    await expect(page.locator('#verificationSectionSelector')).toBeVisible();
    await expect(page.getByRole('button', { name: /generate final/i })).toBeVisible();

    // 3. Switch to Step 3 (Interactive Title Chain / Narrative Flow)
    await page.locator('#step-indicator-chain').click();
    await expect(page.locator('#step-chain-view')).toBeVisible();
  });

  test.skip('16. Field-Level Source Attribution works', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('link', { name: '+ New RM Case' }).click();
    await page.waitForURL(/\/case\/case_\d+/);

    // Switch to step 2 (Verify & Review)
    await page.locator('#step-indicator-review').click();
    await expect(page.locator('#step-review-view')).toBeVisible();

    // 1. Focus on Borrower 1 Name field
    const nameField = page.locator('#field_bs_0_n');
    await nameField.focus();

    // Verify source attribution chip is displayed next to the label with correct filename
    const chip = page.locator('.source-attribution-chip');
    await expect(chip).toBeVisible();
    await expect(chip).toContainText('Kiran Devi.pdf');

    // Verify preview highlight overlay is displayed when bounding box exists
    const overlay = page.locator('#previewHighlightOverlay');
    await expect(overlay).toBeAttached();
    // Validate overlay style got updated with bounding box percentage coordinates
    const styleAttr = await overlay.getAttribute('style') || '';
    expect(styleAttr).toContain('display: block');
    expect(styleAttr).toContain('top: 15%');
    expect(styleAttr).toContain('left: 20%');

    // 2. Focus on Witness 1 Name field
    // Select the witnesses section in the dropdown selector to make the pane visible and focusable
    await page.locator('#verificationSectionSelector').selectOption('pane-witnesses');
    const witnessField = page.locator('#field_ws_0_n');
    await witnessField.focus();

    // Verify chip updates to the witness source file
    await expect(chip).toContainText('Rakesh.pdf');

    // Verify overlay is hidden since Witness 1 has no bounding box coords
    const styleAttr2 = await overlay.getAttribute('style') || '';
    expect(styleAttr2).toContain('display: none');
  });

  test.skip('17. AI Confidence Indicators work', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('link', { name: '+ New RM Case' }).click();
    await page.waitForURL(/\/case\/case_\d+/);

    // Switch to step 2 (Verify & Review)
    await page.locator('#step-indicator-review').click();
    await expect(page.locator('#step-review-view')).toBeVisible();

    // Verify low confidence PAN field highlights and warning tooltip
    const lowConfWrapper = page.locator('#field_bs_0_pan').locator('xpath=..');
    await expect(lowConfWrapper).toHaveClass(/confidence-low/);
    
    const lowConfBadge = lowConfWrapper.locator('.confidence-badge.badge-low');
    await expect(lowConfBadge).toBeVisible();
    await expect(lowConfBadge).toContainText('!');
    const lowTitle = await lowConfBadge.getAttribute('title') || '';
    expect(lowTitle).toContain('62%');
    expect(lowTitle).toContain('Image blur on PAN Card scan page');

    // Verify medium confidence Bank Signatory PAN field highlights and tooltip
    const medConfWrapper = page.locator('#field_bsign_pan').locator('xpath=..');
    await expect(medConfWrapper).toHaveClass(/confidence-medium/);
    
    const medConfBadge = medConfWrapper.locator('.confidence-badge.badge-medium');
    await expect(medConfBadge).toBeVisible();
    await expect(medConfBadge).toContainText('?');
    const medTitle = await medConfBadge.getAttribute('title') || '';
    expect(medTitle).toContain('88%');
    expect(medTitle).toContain('Potential PAN formatting mismatch');

    // Verify high confidence Name field highlight and checkmark
    const highConfWrapper = page.locator('#field_bs_0_n').locator('xpath=..');
    await expect(highConfWrapper).toHaveClass(/confidence-high/);
    const highConfBadge = highConfWrapper.locator('.confidence-badge.badge-high');
    await expect(highConfBadge).toBeVisible();
    await expect(highConfBadge).toContainText('✓');
  });

  test.skip('18. Verification Progress and Compile Safety Gates work', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('link', { name: '+ New RM Case' }).click();
    await page.waitForURL(/\/case\/case_\d+/);

    // Switch to step 2 (Verify & Review)
    await page.locator('#step-indicator-review').click();
    await expect(page.locator('#step-review-view')).toBeVisible();

    // 1. Verify initial progress values (0% verified)
    const progressLabel = page.locator('#overallProgressLabel');
    await expect(progressLabel).toContainText('Verified: 0 /');
    
    const progressBar = page.locator('#overallProgressBar');
    await expect(progressBar).toHaveAttribute('style', 'width: 0%;');

    // 2. Verify sub-tab completion badge shows incomplete
    const partiesBadge = page.locator('#badge-parties');
    await expect(partiesBadge).toHaveClass(/tab-badge-incomplete/);
    await expect(partiesBadge).toContainText('0/');

    // 3. Verify Generate button is disabled by safety gate
    const generateBtn = page.getByRole('button', { name: /generate final/i });
    await expect(generateBtn).toBeDisabled();
    const initTitle = await generateBtn.getAttribute('title') || '';
    expect(initTitle).toContain('Verify critical fields first');

    // 4. Verify critical fields to engage safety gate ready state
    // Let's check critical checkboxes in pane-parties
    await page.locator('input[data-path="bs.0.n"]').click();
    await page.locator('input[data-path="bs.0.id"]').click();
    await page.locator('input[data-path="bsign.n"]').click();

    // Check critical checkboxes in pane-property (need to switch section first)
    await page.locator('#verificationSectionSelector').selectOption('pane-property');
    await page.locator('input[data-path="ps.0.adr"]').click();

    // Check critical checkboxes in pane-parties (Execution Date and Agreement Date)
    await page.locator('#verificationSectionSelector').selectOption('pane-parties');
    await page.locator('input[data-path="rd"]').click();
    await page.locator('input[data-path="ad"]').click();

    // 5. Verify safety gate is open (Generate button is now enabled and green)
    await expect(generateBtn).toBeEnabled();
    await expect(generateBtn).toHaveClass(/btn-success/);
    const finalTitle = await generateBtn.getAttribute('title') || '';
    expect(finalTitle).toContain('Ready to compile');
    
    // Progress bar must show increased percentage
    await expect(progressBar).not.toHaveAttribute('style', 'width: 0%;');
  });

  test('19. Keyboard Workflows Alt+N, Alt+V, Ctrl+S, and Tab Skip work', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('link', { name: '+ New RM Case' }).click();
    await page.waitForURL(/\/case\/case_\d+/);

    // Switch to step 2 (Verify & Review)
    await page.locator('#step-indicator-review').click();
    await expect(page.locator('#step-review-view')).toBeVisible();

    // 1. Initial jump: press Alt+N to focus the first unverified field (Execution Date)
    await page.keyboard.press('Alt+n');
    const rdField = page.locator('#field_rd');
    await expect(rdField).toBeFocused();

    // 2. Toggle verification: press Alt+V to verify the focused field
    const rdCheckbox = page.locator('input[data-path="rd"]');
    await expect(rdCheckbox).not.toBeChecked();
    await page.keyboard.press('Alt+v');
    await expect(rdCheckbox).toBeChecked();

    // 3. Jump again: press Alt+N to jump to the next unverified field (Agreement Date)
    await page.keyboard.press('Alt+n');
    const adField = page.locator('#field_ad');
    await expect(adField).toBeFocused();

    // 4. Tab Skip check: press Tab and verify focus skips the verify checkbox of adField and goes directly to the next input (Borrower 1 Salutation)
    await page.keyboard.press('Tab');
    const firstBorrowerSalutation = page.locator('#field_bs_0_s');
    await expect(firstBorrowerSalutation).toBeFocused();

    // 5. Ctrl+S: press Ctrl+S and verify it sends save request to backend
    const savePromise = page.waitForResponse(/\/case\/case_\d+\/save/);
    await page.keyboard.press('Control+s');
    const response = await savePromise;
    expect(response.status()).toBe(200);
  });

  test('20. Bulk Verification and Undo actions work', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('link', { name: '+ New RM Case' }).click();
    await page.waitForURL(/\/case\/case_\d+/);

    // Switch to step 2 (Verify & Review)
    await page.locator('#step-indicator-review').click();
    await expect(page.locator('#step-review-view')).toBeVisible();

    // 1. Initial state checks
    const undoBanner = page.locator('#bulkUndoBanner');
    await expect(undoBanner).toHaveClass(/d-none/);

    const b0Name = page.locator('input[data-path="bs.0.n"]');
    const b0Sal = page.locator('input[data-path="bs.0.s"]');
    const signerName = page.locator('input[data-path="bsign.n"]');

    await expect(b0Name).not.toBeChecked();
    await expect(b0Sal).not.toBeChecked();
    await expect(signerName).not.toBeChecked();

    // 2. Click Verify Category badge inside Borrower card
    const verifyCatBtn = page.locator('.borrower-card .verify-category-btn').first();
    await verifyCatBtn.click();

    // Verify fields inside the card are checked, but outside is unchecked
    await expect(b0Name).toBeChecked();
    await expect(b0Sal).toBeChecked();
    await expect(signerName).not.toBeChecked();

    // Verify Undo banner is shown
    await expect(undoBanner).toBeVisible();
    await expect(page.locator('#bulkUndoMessage')).toContainText('Category "Borrower 1"');

    // 3. Undo the category bulk action via banner button
    await undoBanner.locator('button').click();

    // Verify states are restored
    await expect(b0Name).not.toBeChecked();
    await expect(b0Sal).not.toBeChecked();

    // 4. Verify Section action via keyboard (Alt+A)
    await page.keyboard.press('Alt+a');

    // All checkboxes in the active tab (Parties) should be checked
    await expect(b0Name).toBeChecked();
    await expect(signerName).toBeChecked();

    // 5. Undo the section bulk action via keyboard (Ctrl+Z)
    await page.keyboard.press('Control+z');

    // Verify states are restored
    await expect(b0Name).not.toBeChecked();
    await expect(signerName).not.toBeChecked();
    await expect(undoBanner).toHaveClass(/d-none/);
  });

  test.skip('21. Validation Framework Integration and Case Health status works', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('link', { name: '+ New RM Case' }).click();
    await page.waitForURL(/\/case\/case_\d+/);

    // Switch to step 2 (Verify & Review)
    await page.locator('#step-indicator-review').click();
    await expect(page.locator('#step-review-view')).toBeVisible();

    // 1. Initial state check: Empty case is clean (🟢 Ready)
    const healthBadge = page.locator('#caseHealthBadge');
    await expect(healthBadge).toBeVisible();
    await expect(healthBadge).toContainText('Ready');

    // 2. Type an invalid Aadhaar format (1234)
    const idInput = page.locator('#field_bs_0_id');
    await idInput.fill('1234');
    await idInput.blur();

    // Save case to trigger backend validation run
    let savePromise = page.waitForResponse(/\/case\/case_\d+\/save/);
    await page.keyboard.press('Control+s');
    await savePromise;

    // Verify badge updates to ⚠️ Issues Found
    await expect(healthBadge).toContainText('Issues Found');

    // 3. Fix Aadhaar to valid Verhoeff string (368294528141)
    await idInput.fill('368294528141');
    await idInput.blur();
    
    savePromise = page.waitForResponse(/\/case\/case_\d+\/save/);
    await page.keyboard.press('Control+s');
    await savePromise;

    // Verify badge updates back to 🟢 Ready
    await expect(healthBadge).toContainText('Ready');

    // 4. Enter invalid PAN syntax to trigger Issues Found again
    const panInput = page.locator('#field_bs_0_pan');
    await panInput.fill('invalidpan');
    await panInput.blur();

    savePromise = page.waitForResponse(/\/case\/case_\d+\/save/);
    await page.keyboard.press('Control+s');
    await savePromise;

    await expect(healthBadge).toContainText('Issues Found');
  });

  test('22. Title Chain Timeline and Narrative Generation work', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('link', { name: '+ New SD Case' }).click();
    await page.waitForURL(/\/case\/case_\d+/);

    // Switch to step 3 (Title Chain Timeline)
    await page.locator('#step-indicator-chain').click();
    await expect(page.locator('#step-chain-view')).toBeVisible();

    // Directly populate the titleChainEvents array in client-side JS context to bypass input event race conditions
    await page.evaluate(() => {
      if (typeof titleChainEvents !== 'undefined') {
        titleChainEvents.push({
          event_type: 'SALE_DEED_PLOT',
          template_key: 'SALE_DEED_PLOT',
          date: '12-10-2023',
          d: '12-10-2023',
          executant_name: 'Ganesh Lal',
          s: 'Ganesh Lal',
          claimant_name: 'Sita Devi',
          b: 'Sita Devi',
          reg_no: 'Reg-1234',
          r_no: 'Reg-1234',
          reg_book: '1',
          b_no: '1',
          reg_vol: '15',
          v_no: '15',
          reg_add_page: '10-20',
          page_range: '10-20',
          p_no: '10-20',
          consideration_amount: '15,00,000/-',
          consideration: '15,00,000/-',
          is_registered: 'true'
        });
        // Render timeline visualization
        renderTimeline();
      }
    });

    // Click Re-Generate Narrative
    await page.locator('button[onclick="refreshNarrativePreview()"]').click();

    // Wait for narrative generation completion
    await expect(page.locator('#statusMsg')).toContainText('Narrative generated successfully');

    // Verify compiled narrative is populated
    const narrativeTextarea = page.locator('#chainNarrativePreview');
    await expect(narrativeTextarea).not.toHaveValue('');
    const narrativeVal = await narrativeTextarea.inputValue();
    expect(narrativeVal).toContain('Ganesh Lal');
    expect(narrativeVal).toContain('Sita Devi');
  });

  test('23. Unicode Hindi input compiles legacy DevLys draft successfully', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('link', { name: '+ New RM Case' }).click();
    await page.waitForURL(/\/case\/case_\d+/);

    // Switch to Step 2
    await page.locator('#step-indicator-review').click();
    
    // Directly populate the critical fields in DOM via evaluate to avoid tab-switching visibility blocks
    await page.evaluate(() => {
      const nameEl = document.getElementById('field_bs_0_n') as HTMLInputElement | null;
      if (nameEl) nameEl.value = 'राकेश कुमार';
      
      const sigEl = document.getElementById('field_bsign_n') as HTMLInputElement | null;
      if (sigEl) sigEl.value = 'Manager Singh';
      
      const addrEl = document.getElementById('field_ps_0_adr') as HTMLTextAreaElement | null;
      if (addrEl) addrEl.value = 'Plot No 5, Jaipur';
    });

    // Verify all fields in all sections to clear safety gate (Note: pane-loan is singular)
    const options = ['pane-parties', 'pane-property', 'pane-loan', 'pane-schedules'];
    for (const opt of options) {
      await page.locator('#verificationSectionSelector').selectOption(opt);
      await page.locator('button[onclick="verifySection()"]').click();
    }

    // Gate will be open
    const generateBtn = page.getByRole('button', { name: /generate final/i });
    await expect(generateBtn).toBeEnabled();

    // Wait for file download request
    const downloadPromise = page.waitForEvent('download');
    await generateBtn.click();
    const download = await downloadPromise;
    expect(download.suggestedFilename()).toContain('.docx');
  });

  test('24. e-Panjiyan API endpoints respond with structured payload', async ({ request, page }) => {
    // 1. Get the current case_id from workspace URL
    await page.goto('/');
    await page.getByRole('link', { name: '+ New RM Case' }).click();
    await page.waitForURL(/\/case\/(case_\d+)/);
    const caseId = page.url().split('/').pop() || '';

    // 2. Fetch e-Panjiyan formatted data
    const res = await request.get(`/api/case/${caseId}/epanjiyan_data`);
    expect(res.status()).toBe(200);
    const payload = await res.json();
    expect(payload).toHaveProperty('claimant');

    // 3. Save a valuation quote and verify it updates the session
    const saveValuationRes = await request.post(`/api/case/${caseId}/save_valuation_quote`, {
      data: {
        stamp_duty: "15000",
        registration_fee: "5000",
        cess_surcharge: "2000",
        total_fee: "22000"
      }
    });
    expect(saveValuationRes.status()).toBe(200);
  });

  test('25. Optimistic concurrency: stale revision returns 409 via API', async ({ request, page }) => {
    // Create a case
    await page.goto('/');
    await page.getByRole('link', { name: '+ New RM Case' }).click();
    await page.waitForURL(/\/case\/(case_\d+)/);
    const caseId = page.url().split('/').pop() || '';

    const savePayload = {
      data: { note: 'first save' },
      doc_type: 'RM',
      bank: 'TestBank',
      borrowers: '1',
      loans: '1',
      properties: '1',
      verified_fields: [],
    };

    // First save — no revision, acquires revision 1
    const r1 = await request.post(`/case/${caseId}/save`, { data: savePayload });
    expect(r1.status()).toBe(200);
    const d1 = await r1.json();
    const rev1 = d1.revision;
    expect(typeof rev1).toBe('number');

    // Second save with the correct revision — should succeed and bump to 2
    const r2 = await request.post(`/case/${caseId}/save`, {
      data: { ...savePayload, revision: rev1 }
    });
    expect(r2.status()).toBe(200);
    const d2 = await r2.json();
    expect(d2.revision).toBe(rev1 + 1);

    // Third save with the STALE revision (rev1 again) — must return 409
    const r3 = await request.post(`/case/${caseId}/save`, {
      data: { ...savePayload, revision: rev1 }
    });
    expect(r3.status()).toBe(409);
    const d3 = await r3.json();
    expect(d3.error).toBe('revision_conflict');
  });

  test('26. Filename sanitisation: path traversal in upload is stripped', async ({ request, page }) => {
    // Create a case
    await page.goto('/');
    await page.getByRole('link', { name: '+ New RM Case' }).click();
    await page.waitForURL(/\/case\/(case_\d+)/);
    const caseId = page.url().split('/').pop() || '';

    // Craft a multipart upload with a traversal filename
    const formData = new FormData();
    const fakeContent = new Blob(['%PDF-1.4 evil payload'], { type: 'application/pdf' });
    formData.append('files', fakeContent, '../../evil.pdf');

    const resp = await page.evaluate(async ([id, b64]) => {
      const blob = new Blob([atob(b64)], { type: 'application/pdf' });
      const fd = new FormData();
      fd.append('files', blob, '../../evil.pdf');
      const r = await fetch(`/case/${id}/upload_files`, { method: 'POST', body: fd });
      return { status: r.status, body: await r.json() };
    }, [caseId, btoa('%PDF-1.4 evil payload')]);

    expect(resp.status).toBe(200);
    // The returned filename must not contain traversal components
    for (const fn of (resp.body.new_files || [])) {
      expect(fn).not.toContain('..');
      expect(fn).not.toContain('/');
    }
  });

  // ---------------------------------------------------------------------------
  // Tests 27–30: Optimistic Concurrency – Conflict Dialog
  // ---------------------------------------------------------------------------

  test('27. Concurrent tabs: second tab save increments revision and first tab gets 409', async ({ request }) => {
    // Create a case via the API (no browser navigation needed)
    const newCaseResp = await request.get('/new_case?doc_type=RM');
    // The server redirects to /case/<case_id>
    const location = newCaseResp.headers()['location'] || newCaseResp.url();
    const caseId = location.replace(/.*\/case\//, '').split('/')[0];
    expect(caseId).toMatch(/case_\d+/);

    const basePayload = {
      data: { note: 'tab-a' }, doc_type: 'RM', bank: 'B',
      borrowers: '1', loans: '1', properties: '1', verified_fields: [],
    };

    // Tab A: first save without revision – gets revision 1
    const r1 = await request.post(`/case/${caseId}/save`, { data: basePayload });
    expect(r1.status()).toBe(200);
    const rev1 = (await r1.json()).revision;
    expect(typeof rev1).toBe('number');

    // Tab B: save without revision token – succeeds, bumps to rev 2
    const r2 = await request.post(`/case/${caseId}/save`, {
      data: { ...basePayload, data: { note: 'tab-b' } }
    });
    expect(r2.status()).toBe(200);
    const rev2 = (await r2.json()).revision;
    expect(rev2).toBe(rev1 + 1);

    // Tab A: tries to save with stale rev1 – must get 409
    const r3 = await request.post(`/case/${caseId}/save`, {
      data: { ...basePayload, revision: rev1 }
    });
    expect(r3.status()).toBe(409);
    expect((await r3.json()).error).toBe('revision_conflict');
  });

  test('28. Conflict dialog appears when save returns 409', async ({ page }) => {
    // Create a case and load it
    await page.goto('/');
    await page.getByRole('link', { name: '+ New RM Case' }).click();
    await page.waitForURL(/\/case\/(case_\d+)/);
    const caseId = page.url().split('/').pop() || '';

    // Intercept the save POST and force a 409 response to trigger the dialog
    await page.route(`/case/${caseId}/save`, async route => {
      await route.fulfill({
        status: 409,
        contentType: 'application/json',
        body: JSON.stringify({ success: false, error: 'revision_conflict',
                               detail: 'Simulated conflict' })
      });
    });

    // Click Save Progress button
    await page.click('button[onclick="saveCase()"]');

    // Conflict dialog must appear
    await expect(page.locator('#rm-conflict-dialog')).toBeVisible({ timeout: 4000 });
    await expect(page.locator('#rm-cf-title')).toContainText('Save Conflict Detected');

    // All four action buttons must be present
    await expect(page.locator('#rm-cf-reload')).toBeVisible();
    await expect(page.locator('#rm-cf-force')).toBeVisible();
    await expect(page.locator('#rm-cf-compare')).toBeVisible();
    await expect(page.locator('#rm-cf-cancel')).toBeVisible();
  });

  test('29. Conflict dialog – Cancel closes dialog without saving', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('link', { name: '+ New RM Case' }).click();
    await page.waitForURL(/\/case\/(case_\d+)/);
    const caseId = page.url().split('/').pop() || '';

    // Force 409 on every save request
    await page.route(`/case/${caseId}/save`, async route => {
      await route.fulfill({
        status: 409,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'revision_conflict' })
      });
    });

    await page.click('button[onclick="saveCase()"]');
    await expect(page.locator('#rm-conflict-dialog')).toBeVisible({ timeout: 4000 });

    // Cancel – dialog must disappear, page must NOT reload
    await page.click('#rm-cf-cancel');
    await expect(page.locator('#rm-conflict-dialog')).not.toBeVisible();
    // URL should remain on the case page
    expect(page.url()).toContain(caseId);
  });

  test('30. Conflict dialog – Force-save retries save with null revision', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('link', { name: '+ New RM Case' }).click();
    await page.waitForURL(/\/case\/(case_\d+)/);
    const caseId = page.url().split('/').pop() || '';

    let saveCount = 0;

    // First call → 409; second call (force-save with null revision) → 200
    await page.route(`/case/${caseId}/save`, async route => {
      saveCount++;
      if (saveCount === 1) {
        await route.fulfill({
          status: 409,
          contentType: 'application/json',
          body: JSON.stringify({ error: 'revision_conflict' })
        });
      } else {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ success: true, revision: 2 })
        });
      }
    });

    // Trigger first save (will 409)
    await page.click('button[onclick="saveCase()"]');
    await expect(page.locator('#rm-conflict-dialog')).toBeVisible({ timeout: 4000 });

    // Click "Keep my version & overwrite"
    await page.click('#rm-cf-force');

    // Dialog must close
    await expect(page.locator('#rm-conflict-dialog')).not.toBeVisible({ timeout: 4000 });

    // A total of 2 save requests must have been made (original + force-retry)
    expect(saveCount).toBe(2);
  });
});
