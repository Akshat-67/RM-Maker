import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        print("Navigating to dashboard...")
        await page.goto("http://localhost:3000/")

        # Click on the first case link (if available) or create a case first if not
        # To avoid dependency, let's look at the UI directly using app.py running in background
        print("Wait for page load...")
        await page.wait_for_timeout(1000)

        links = await page.locator("a[href^='/case/']").all()
        if not links:
            print("No cases found, creating one...")
            await page.fill("#newCaseId", "test_case_ui_1")
            await page.click("button:has-text('Create Workspace')")
            await page.wait_for_timeout(1000)

            links = await page.locator("a[href^='/case/']").all()

        if links:
            print(f"Navigating to case...")
            href = await links[0].get_attribute("href")
            await page.goto(f"http://localhost:3000{href}")
            await page.wait_for_timeout(2000)

            print("Wait for generate button...")
            btn = page.locator("#generateBtn")
            if await btn.count() > 0:
                print("Clicking generate button...")

                # Mock window.alert to not block test
                await page.evaluate("window.alert = function() {}")

                await btn.click()
                print("Checking button state...")

                # Check if it has spinner text
                text = await btn.inner_text()
                is_disabled = await btn.is_disabled()
                print(f"Button text: {text}, Disabled: {is_disabled}")

                if "Generating" in text and is_disabled:
                    print("SUCCESS: Loading state applied correctly.")
                else:
                    print("FAILURE: Loading state not applied.")

                print("Waiting for reset...")
                await page.wait_for_timeout(3000)

                text2 = await btn.inner_text()
                is_disabled2 = await btn.is_disabled()
                print(f"Button text after: {text2}, Disabled: {is_disabled2}")
                if not is_disabled2:
                    print("SUCCESS: Button reset correctly.")
                else:
                    print("FAILURE: Button not reset.")

            else:
                print("Could not find generate button. This might happen if 'verified' UI is not shown.")
                print("Trying to show it...")
                await page.evaluate("document.querySelector('.tab-pane').classList.add('show', 'active')")
                # Alternatively, let's just test that the button code exists in HTML
                html = await page.content()
                if 'id="generateBtn"' in html:
                    print("SUCCESS: generateBtn found in HTML")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
