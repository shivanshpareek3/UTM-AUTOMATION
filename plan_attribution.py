import pandas as pd
import numpy as np

# Suppose we have sales:
sales = pd.DataFrame([
    {'id': 1, 'camp_norm': 'c1', 'adset_norm': 'as1', 'ad_norm': 'ad1', 'match_level': 'Ad Level'},
    {'id': 2, 'camp_norm': 'c1', 'adset_norm': 'as1', 'ad_norm': 'ad2', 'match_level': 'Ad Level'},
    {'id': 3, 'camp_norm': 'c1', 'adset_norm': 'as2', 'ad_norm': '',    'match_level': 'Adset Level'},
    {'id': 4, 'camp_norm': 'c1', 'adset_norm': '',    'match_level': 'Campaign Level'},
])

# If Meta spend is Campaign only:
meta = pd.DataFrame([
    {'camp_norm': 'c1', 'Amount Spent': 1000}
])
