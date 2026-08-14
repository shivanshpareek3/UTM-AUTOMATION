from playwright.sync_api import sync_playwright
import time

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("http://localhost:8501")
        time.sleep(3)
        
        # Upload files
        page.locator("input[type='file']").nth(0).set_input_files("/Users/apple/Downloads/12-08-2026_leads.csv")
        page.locator("input[type='file']").nth(1).set_input_files("/Users/apple/Downloads/12-08-2026_sales(1).csv")
        page.locator("input[type='file']").nth(2).set_input_files("/Users/apple/Downloads/FML-X-Satyam-2-Campaigns-1-Aug-2026-12-Aug-2026.csv")
        time.sleep(5)
        
        # Select custom preset
        page.locator("div[data-testid='stSelectbox']").first.click()
        page.locator("li[role='option']:has-text('Custom')").click()
        time.sleep(1)
        
        # Type dates
        inputs = page.locator("input[data-baseweb='input']")
        # The first input is Lead / Sales Start Date
        inputs.nth(0).fill("2026/08/01")
        inputs.nth(0).press("Enter")
        time.sleep(1)
        inputs.nth(1).fill("2026/08/12")
        inputs.nth(1).press("Enter")
        time.sleep(1)
        
        inputs.nth(2).fill("2026/08/01")
        inputs.nth(2).press("Enter")
        time.sleep(1)
        inputs.nth(3).fill("2026/08/12")
        inputs.nth(3).press("Enter")
        time.sleep(2)
        
        # Click Generate Report
        page.click("button:has-text('🚀 Generate Report')")
        time.sleep(3)
        
        # Check for error
        if page.locator("div.stException").count() > 0:
            print("ERROR FOUND:")
            print(page.locator("div.stException").inner_text())
        else:
            print("No error on UI with Custom dates!")
            
        browser.close()

run()
