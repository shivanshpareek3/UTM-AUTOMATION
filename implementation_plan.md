# Fix Meta Spend Attribution Layer

The bug in the application is that it forces 100% of an Ad's/AdSet's/Campaign's spend to be attributed as long as there is at least 1 sale in that bucket. It pools "wasted" spend from unconverted leads and forces it onto the successful sales, which artificially inflates the Attributed Spend and leaves almost nothing as Unallocated.

## Root Cause in `src/spend.py`
Currently, the code calculates `allocated_spend` by taking the entire `Amount Spent` slice and dividing it by `sales_count`.
```python
ad_merged['allocated_spend'] = ad_merged.apply(lambda r: r['Amount Spent'] if r['sales_count'] > 0 else 0.0, axis=1)
```
This violates the "Lead-Share %" methodology from the Golden Manual Report. 

In the manual methodology, spend is proportional to the lead population:
- `Campaign CPL = Raw Campaign Spend / Campaign Leads`
- Each lead inherently costs `Campaign CPL`.
- When a lead converts to a sale, it brings its `Campaign CPL` as the **Attributed Spend**.
- The unconverted leads' spend remains **Unallocated**.

Mathematically, this means:
- `Attributed Spend = Campaign Spend * (Paid Leads / Campaign Leads)`
- `Unallocated Spend = Campaign Spend * (Unpaid Leads / Campaign Leads)`

## Proposed Changes

### `src/spend.py`
[MODIFY] [src/spend.py](file:///Users/apple/Desktop/UTM%20automation/src/spend.py)
Rewrite `allocate_spend` to implement the correct Lead-Share proportional methodology.
1. Calculate `Campaign CPL` = `Campaign Spend / Campaign Leads`.
2. For every matched sale (Paid Lead), its `attributed_spend` is exactly the `Campaign CPL` of its matched campaign.
3. This inherently and correctly builds the Ad Set and Ad Creative level summaries because a sale mapped to an Ad brings its `Campaign CPL` into that Ad's attributed spend, perfectly matching `Ad Spend * (Ad Paid Leads / Ad Leads)`.
4. Unallocated spend naturally drops out as the spend of leads that didn't convert.

### `src/metrics.py`
[MODIFY] [src/metrics.py](file:///Users/apple/Desktop/UTM%20automation/src/metrics.py)
Ensure that the financial metrics dynamically use the corrected `attributed_spend`:
- `profit = attributed_revenue - attributed_spend`
- `roas = attributed_revenue / attributed_spend`
- `roi = (profit / attributed_spend) * 100`
- `cac = attributed_spend / attributed_sales`
These formulas are already mostly correct, but we will ensure they safely handle 0 and produce the required outputs.

## User Review Required
> [!IMPORTANT]
> The current pooling logic cascades wasted spend up the hierarchy. The new logic will completely remove this cascading pool and strictly allocate spend based on `(Paid Leads / Total Leads)`. Please confirm this matches the exact manual Golden Report behavior.

## Verification Plan
1. Run the test suite (`pytest tests/`) to ensure no regressions.
2. Run the application pipeline and generate the Excel report.
3. Verify that the Dashboard and Excel report dynamically reflect the corrected ROAS, ROI, and CAC formulas using the new Attributed Spend logic.
