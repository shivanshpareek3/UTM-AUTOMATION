import time
import random
import string
from difflib import SequenceMatcher

def random_string(length):
    return ''.join(random.choices(string.ascii_lowercase, k=length))

lead_emails = [random_string(random.randint(10, 30)) + "@gmail.com" for _ in range(10000)]
sales_emails = [random_string(random.randint(10, 30)) + "@gmail.com" for _ in range(50)]

# Old method
t0 = time.time()
best_matches_old = {}
for se in sales_emails:
    best_match = None
    best_score = 0
    for le in lead_emails:
        score = SequenceMatcher(None, se, le).ratio()
        if score > best_score:
            best_score = score
            best_match = le
    if best_score > 0.95:
        best_matches_old[se] = best_match
t1 = time.time()
print(f"Old method took {t1 - t0:.4f} seconds")

# New method (length blocking)
t0 = time.time()
leads_by_len = {}
for le in lead_emails:
    leads_by_len.setdefault(len(le), []).append(le)

best_matches_new = {}
for se in sales_emails:
    L1 = len(se)
    best_match = None
    best_score = 0
    for L2, group in leads_by_len.items():
        if 2 * min(L1, L2) / (L1 + L2) > 0.95:
            for le in group:
                score = SequenceMatcher(None, se, le).ratio()
                if score > best_score:
                    best_score = score
                    best_match = le
    if best_score > 0.95:
        best_matches_new[se] = best_match
t1 = time.time()
print(f"New method (length blocking) took {t1 - t0:.4f} seconds")

# Ensure identical results
print(best_matches_old == best_matches_new)
