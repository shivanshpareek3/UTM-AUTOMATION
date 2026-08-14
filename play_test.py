from playwright.sync_api import sync_playwright
import time
import os
import pandas as pd

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("http://localhost:8505")
        
        print("Waiting for file inputs...")
        page.wait_for_selector('input[type="file"]', state="attached", timeout=30000)
        file_inputs = page.locator('input[type="file"]')
        
        print("Uploading files...")
        file_inputs.nth(0).set_input_files('/Users/apple/Downloads/12-08-2026_leads.csv')
        time.sleep(1)
        file_inputs.nth(1).set_input_files('/Users/apple/Downloads/12-08-2026_sales(1).csv')
        time.sleep(1)
        file_inputs.nth(2).set_input_files([
            '/Users/apple/Downloads/FML-X-Satyam-2-Campaigns-1-Aug-2026-12-Aug-2026.csv',
            '/Users/apple/Downloads/SSA-X-SATYAM-KHANDELWAL-Campaigns-1-Aug-2026-12-Aug-2026.csv'
        ])
        print("Waiting for mapping to finish processing...")
        time.sleep(5)
        
        # Verify detected dates
        print("Verifying date detection UI...")
        try:
            page.wait_for_selector("text=2026-08-12", timeout=10000)
            print("Date detection PASS")
        except:
            print("Date detection FAIL (or text not found)")
        # Wait for the Start Date input to appear
        page.wait_for_selector('div[data-testid="stDateInput"]', timeout=30000)
        
        # Select dates (Aug 1 - 12)
        print("Selecting dates (Aug 1 - 12)...")
        # Lead/Sales dates
        starts = page.locator('div[data-testid="stDateInput"]:has-text("Start Date") input')
        ends = page.locator('div[data-testid="stDateInput"]:has-text("End Date") input')
        
        starts.nth(0).fill("2026/08/01")
        ends.nth(0).fill("2026/08/12")
        
        # Meta dates
        starts.nth(1).fill("2026/08/01")
        ends.nth(1).fill("2026/08/12")
        
        print("Clicking Generate Report...")
        page.click("button:has-text('🚀 Generate Report')")
        
        print("Waiting for validation...")
        page.wait_for_selector("text=REPORT VALID", state="attached", timeout=30000)
        
        print("Downloading first Excel...")
        with page.expect_download() as download_info:
            page.click("button:has-text('Download Excel Workbook')")
        d1 = download_info.value
        path1 = os.path.abspath("test_output1.xlsx")
        d1.save_as(path1)
        print(f"First Excel path: {path1}")
        
        print("Selecting dates (Aug 5 - 10)...")
        starts.nth(0).fill("2026/08/05")
        starts.nth(1).fill("2026/08/05")
        ends.nth(0).fill("2026/08/10")
        ends.nth(1).fill("2026/08/10")
        
        print("Clicking Generate Report again...")
        # Since the button is the same, just click it again
        page.click("button:has-text('🚀 Generate Report')")
        time.sleep(2) # wait for re-run to start
        page.wait_for_selector("text=REPORT VALID", state="attached", timeout=30000)
        
        print("Downloading second Excel...")
        with page.expect_download() as download_info2:
            page.click("button:has-text('Download Excel Workbook')")
        d2 = download_info2.value
        path2 = os.path.abspath("test_output2.xlsx")
        d2.save_as(path2)
        print(f"Second Excel path: {path2}")
        
        # Read the files to extract metrics
        df1 = pd.read_excel(path1, sheet_name="1. ⚙ Settings & Run Log")
        print("\n--- FIRST REPORT METRICS (Aug 1 - 12) ---")
        print(df1)
        
        df2 = pd.read_excel(path2, sheet_name="1. ⚙ Settings & Run Log")
        print("\n--- SECOND REPORT METRICS (Aug 5 - 10) ---")
        print(df2)
        
        browser.close()

if __name__ == '__main__':
    run()
