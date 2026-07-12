from playwright.sync_api import sync_playwright
import time

def test_title_chain():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            print("Navigating to dashboard...")
            page.goto("http://127.0.0.1:5000/", wait_until="networkidle")
            
            print("Creating new SD case...")
            page.click('text="+ New SD Case"')
            page.wait_for_load_state("networkidle")
            
            print("Adding a Title Chain Event...")
            # Click add title event button
            page.click('text="➕ Add Title Event"')
            page.wait_for_timeout(500)
            
            # Fill fields
            page.fill('input[id$="_document_name"]', 'पट्टा')
            page.fill('input[id$="_claimant_name"]', 'राम सिंह')
            page.fill('input[id$="_date"]', '10.10.2010')
            
            print("Waiting for preview to update...")
            page.wait_for_timeout(2000)
            
            preview_text = page.locator('#chainPreviewContent').inner_text()
            print(f"\n--- PREVIEW CONTENT ---\n{preview_text}\n-----------------------\n")
            
        except Exception as e:
            print(f"Error: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    test_title_chain()
