from playwright.sync_api import sync_playwright
import time
import os

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("http://localhost:8501")
        time.sleep(5)
        
        # Upload Leads
        page.locator("input[type='file']").nth(0).set_input_files("/Users/apple/Downloads/12-08-2026_leads.csv")
        time.sleep(2)
        
        # Upload Sales
        page.locator("input[type='file']").nth(1).set_input_files("/Users/apple/Downloads/12-08-2026_sales(1).csv")
        time.sleep(2)
        
        # Upload Meta
        page.locator("input[type='file']").nth(2).set_input_files("/Users/apple/Downloads/FML-X-Satyam-2-Campaigns-1-Aug-2026-12-Aug-2026.csv")
        time.sleep(5)
        
        # Generate Report
        page.click("button:has-text('🚀 Generate Report')")
        time.sleep(5)
        
        # Check for error
        if page.locator("div.stException").count() > 0:
            print("ERROR FOUND:")
            print(page.locator("div.stException").inner_text())
        else:
            print("No error on UI!")
            
        browser.close()

run()
