import pandas as pd

blind = pd.read_csv("validation_blind.csv")
key = pd.read_csv("validation_key.csv")

merged = blind.merge(key, on="reviewId")
merged["your_tag"] = merged["your_tag"].str.strip().str.upper()

# separate junk rows: human-only category
junk = merged[merged["your_tag"] == "JUNK"]
scored = merged[merged["your_tag"] != "JUNK"]

agree = (scored["your_tag"] == scored["primary_tag"]).sum()
total = len(scored)

print(f"JUNK rows (excluded from agreement): {len(junk)}")
print(f"Agreement: {agree}/{total} = {agree/total:.1%}\n")

print("=== DISAGREEMENTS ===")
dis = scored[scored["your_tag"] != scored["primary_tag"]]
for _, r in dis.iterrows():
    print(f"You: {r.your_tag:20s} AI: {r.primary_tag:20s} | {str(r.content)[:120]}")