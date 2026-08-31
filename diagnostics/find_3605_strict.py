import glob
import pandas as pd

files = glob.glob("/Users/apple/Desktop/UTM automation/*.csv") + glob.glob("/Users/apple/Desktop/UTM automation/*.xlsx")
for f in files:
    try:
        if f.endswith('.csv'):
            df = pd.read_csv(f)
        else:
            df = pd.read_excel(f)
        if len(df) == 3605:
            print(f"FOUND 3605 in {f}")
    except:
        pass
