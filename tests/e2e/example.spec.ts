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

  test('8. Template builder loads', async ({ page }) => {
    // Direct navigation to Template Builder page
    await page.goto('/template-builder');
    
    // Verify page title and header panels
    await expect(page).toHaveTitle(/Template Builder | LegalDoc Automator Pro/);
    await expect(page.getByRole('heading', { name: '1. Setup Mode' })).toBeVisible();
    await expect(page.getByRole('heading', { name: '2. Mapping Workspace' })).toBeVisible();
    
    // Check mode and model selectors exist
    await expect(page.locator('#modeSelect')).toBeVisible();
    await expect(page.locator('#modelSelect')).toBeVisible();
    await expect(page.locator('#fieldCatalog')).toBeVisible();
  });

  /* --- Dedicated Smoke Tests protecting case.html --- */

  test('9. Upload buttons respond', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('link', { name: '+ New SD Case' }).click();
    await page.locator('#step-indicator-upload').click();

    // Verify KYC dropzone is clickable and responds by opening a file chooser
    const [fileChooser] = await Promise.all([
      page.waitForEvent('filechooser'),
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
    await page.getByRole('link', { name: '+ New RM Case' }).click();
    
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
});
