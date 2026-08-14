import pandas as pd
leads = pd.read_csv('/Users/apple/Downloads/12-08-2026_leads.csv')
print("Sample Order Date values:")
print(leads['Order Date'].head(10))
print("Sample sale_date values from Sales:")
sales = pd.read_csv('/Users/apple/Downloads/12-08-2026_sales(1).csv')
print(sales['Order Date'].head(10))
