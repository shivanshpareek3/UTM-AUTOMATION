from playwright.sync_api import sync_playwright
import time

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("http://localhost:8501")
        
        page.wait_for_selector('input[type="file"]', state="attached", timeout=30000)
        file_inputs = page.locator('input[type="file"]')
        
        file_inputs.nth(0).set_input_files('/Users/apple/Downloads/12-08-2026_leads.csv')
        time.sleep(1)
        file_inputs.nth(1).set_input_files('/Users/apple/Downloads/12-08-2026_sales(1).csv')
        time.sleep(1)
        file_inputs.nth(2).set_input_files([
            '/Users/apple/Downloads/FML-X-Satyam-2-Campaigns-1-Aug-2026-12-Aug-2026.csv',
            '/Users/apple/Downloads/SSA-X-SATYAM-KHANDELWAL-Campaigns-1-Aug-2026-12-Aug-2026.csv'
        ])
        
        time.sleep(5) # Wait for processing
        
        html = page.content()
        with open("ui_after_upload.html", "w") as f:
            f.write(html)
            
        browser.close()

if __name__ == '__main__':
    run()
