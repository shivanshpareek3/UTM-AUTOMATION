import pandas as pd
df1 = pd.DataFrame({'A': [1, 2, 3]})
df2 = df1.copy()
df2['A'] = [4, 5, 6]
print("df1 after df2 modified:")
print(df1)
