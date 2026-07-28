import pandas as pd
import ast

df = pd.read_csv("tagged_full.csv")
signal = df[df.primary_tag != "SERVICE_NOISE"]

print("=== Tag distribution BY SOURCE ===")
print(pd.crosstab(df.primary_tag, df.source))

print("\n=== TRUST_QUALITY: which categories? ===")
tq = df[df.primary_tag == "TRUST_QUALITY"]
cats = {}
for c in tq.categories_mentioned.dropna():
    for item in ast.literal_eval(c):
        cats[item] = cats.get(item, 0) + 1
print(sorted(cats.items(), key=lambda x: -x[1]))

print("\n=== TRUST_AUTHENTICITY: which categories? ===")
ta = df[df.primary_tag == "TRUST_AUTHENTICITY"]
cats = {}
for c in ta.categories_mentioned.dropna():
    for item in ast.literal_eval(c):
        cats[item] = cats.get(item, 0) + 1
print(sorted(cats.items(), key=lambda x: -x[1]))

print("\n=== EXPLORED_NEW == True (the gold rows) ===")
gold = df[df.explored_new == True]
print(f"count: {len(gold)}")
for _, r in gold.iterrows():
    print(f"[{r.source} | {r.primary_tag}] {str(r.content)[:200]}\n")