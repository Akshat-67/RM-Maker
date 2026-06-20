import asyncio
from playwright.async_api import async_playwright
import sys

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            print("Navigating to dashboard...")
            response = await page.goto('http://127.0.0.1:5000/')
            if response.status != 200:
                print(f"Failed to load dashboard. Status: {response.status}")
                sys.exit(1)
            print("Dashboard loaded successfully.")

            # Use appropriate URL based on dashboard href for 'new_case'
            print("Clicking new case button to check case.html...")
            # href="{{ url_for('new_case', doc_type='RM') }}" in dashboard.html maps to /new_case?doc_type=RM or /case/new?doc_type=RM. Let's just click it
            await page.click('a.btn-success:has-text("New RM Case")')
            await page.wait_for_load_state('networkidle')
            print("New RM Case loaded successfully.")

            # verify save button exists
            btn = await page.locator('#saveWorkspaceBtn').count()
            if btn == 0:
                print("Save button not found.")
                sys.exit(1)
            print("Save button found.")

            # verify generate button exists
            # Note: For RM, the button text is different but it still has id generateBtn. Let's check.
            btn = await page.locator('#generateBtn').count()
            if btn == 0:
                print("Generate button not found.")
                sys.exit(1)
            print("Generate button found.")

            print("UI Verification Passed.")

        except Exception as e:
            print(f"Error during verification: {e}")
            sys.exit(1)
        finally:
            await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
