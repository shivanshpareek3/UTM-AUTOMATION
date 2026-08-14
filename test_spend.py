import pandas as pd
df = pd.DataFrame({'campaign': ['A', 'B']})
print("get string default:")
df['adset_norm'] = df.get('ad_set', "").apply(lambda x: str(x))
print(df)
