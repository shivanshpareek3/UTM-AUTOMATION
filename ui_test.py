import asyncio
from playwright.async_api import async_playwright
import time

async def run_ui_test():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        print("Navigating to Streamlit app...")
        await page.goto("http://localhost:8502")
        
        # Wait for Streamlit to load
        await page.wait_for_selector("text=🚀 UTM Sales Attribution")
        print("App loaded successfully.")
        
        # We need to find the file uploaders
        # Streamlit file uploaders are <input type="file">
        file_inputs = await page.locator("input[type='file']").all()
        if len(file_inputs) >= 3:
            print("Found file uploaders.")
            # 1. Leads
            await file_inputs[0].set_input_files("/Users/apple/Downloads/Lead Sheet Abhishek pal .csv")
            # 2. Sales
            await file_inputs[1].set_input_files("/Users/apple/Downloads/Sales .csv")
            # 3. Meta
            await file_inputs[2].set_input_files([
                "/Users/apple/Downloads/FML-X-ABHISHEK-PAL-Ad-account-Report.xlsx",
                "/Users/apple/Downloads/Abhishek-Pal-FML-Ad-account-Report.xlsx"
            ])
            print("Files uploaded.")
        else:
            print(f"Error: Found only {len(file_inputs)} file inputs.")
            return

        # Wait for mapping or generate button
        try:
            await page.wait_for_selector("text=Input Inspection & Column Mapping", timeout=15000)
            print("Inspection section appeared.")
        except Exception as e:
            print("Could not find Inspection section.")
            await page.screenshot(path="screenshot.png")
        
        # Fill out settings using placeholders or labels
        # Wait for the "Generate Report" button to be visible
        try:
            generate_btn = page.locator("button:has-text('Generate Report')")
            await generate_btn.wait_for(state="visible", timeout=10000)
            print("Clicking Generate Report...")
            await generate_btn.click()
            
            # Wait for Verification Results
            await page.wait_for_selector("text=Verification Result", state="attached", timeout=30000)
            print("Verification Result appeared!")
            
            # Check for PASS
            passes = await page.locator("text=✅ PASS").count()
            print(f"Found {passes} PASS checks.")
            
            # Check for Download button
            download_btn = page.locator("button:has-text('Download')")
            await download_btn.wait_for(state="visible", timeout=5000)
            print("Download button is enabled!")
            
            print("UI TEST: PASS")
        except Exception as e:
            print(f"UI TEST FAILED: {str(e)}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_ui_test())
