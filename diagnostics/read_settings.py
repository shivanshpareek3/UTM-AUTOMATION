import pandas as pd

try:
    df = pd.read_excel('output/real_data_report.xlsx', sheet_name='1. ⚙ Settings & Run Log')
    print(df.to_string())
except Exception as e:
    print(e)
    try:
        df = pd.read_excel('golden_report.xlsx', sheet_name='1. ⚙ Settings & Run Log')
        print(df.to_string())
    except Exception as e:
        print(e)
