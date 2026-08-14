# UTM Sales Attribution & Profitability Report Generator

A robust internal automation tool for processing Meta Ads Spend, Marketing Leads, and Sales exports to generate a highly accurate, UTM-based attribution and profitability Excel report.

## 🚀 Features
- **4-Level UTM Attribution:** Exact Match > Campaign Match > AdSet Match > Unattributed.
- **Strict Spend Allocation:** 3-tier proportional waterfall allocation ensures every cent of Meta spend is mapped to valid sales without double counting. Total Attributed Spend strictly invariant.
- **Funnel Metrics Engine:** Calculates True ROI, ROAS, CAC, CPL, separating Free vs. Paid webinar sales.
- **Verification Engine:** 9 mandatory data invariants continuously checked to ensure report validity.
- **Excel Report Generator:** Generates a professional 12-sheet Excel report with built-in conditional formatting.

## 💻 Tech Stack
- **Python 3.13+**
- **Pandas** (Data processing)
- **OpenPyXL** (Excel formatting)
- **Streamlit** (UI orchestration)

## 📦 Installation
1. Ensure Python 3.13+ is installed.
2. Clone this repository.
3. Install dependencies:
```bash
pip install -r requirements.txt
```

## 🖥 Running the Application
To launch the Streamlit UI, run:
```bash
python3 -m streamlit run app/streamlit_app.py
```
This will open the interface in your default web browser.

## 📂 Input Files
You must upload exactly these files in CSV or XLSX format:
1. **Leads File:** Must contain `email`, `registration_date`, `webinar_type`, `registration_fee`, `utm_source`, `utm_medium`, `utm_content`.
2. **Sales File:** Must contain `email`, `sale_date`, `order_amount`, `payment_status`. (Failed/refunded sales are excluded).
3. **Meta Spend Files:** You can upload multiple CSVs (from different Ad accounts). Must contain `Campaign Name`, `Ad Set Name`, `Ad Name`, `Amount Spent`, `Day`.

## ⚙ Settings
Configure via the sidebar:
- **Reporting Dates:** Start/End bounds to filter Meta spend and registrations.
- **Cutoff Date:** Used to classify leads as "Old" (registered before) vs "New" (registered on/after).
- **Fallback Price:** Applied if a successful sale row has 0 or missing revenue.
- **Zero-ROI Threshold:** Any campaign spending more than this with 0 sales will be flagged as waste.

## ✅ Verification
The engine runs 9 strict mathematical invariant checks before releasing the Excel file. If *any* check fails (e.g., Attributed Spend exceeds Meta Spend), the report is immediately blocked and marked **INVALID**.

## 🛠 Troubleshooting
If you encounter missing column errors, verify your column names against `config/aliases.json` or update the mapping. Corrupt Excel files will be caught by the ingestor.
