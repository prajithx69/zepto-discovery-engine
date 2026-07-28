# make_validation_sample.py
import pandas as pd

df = pd.read_csv("tagged_full.csv")
sample = df.sample(50, random_state=42)

# blind copy for you: no AI tags visible
blind = sample[["reviewId", "content"]].copy()
blind["your_tag"] = ""
blind.to_csv("validation_blind.csv", index=False)

# answer key stays separate
sample[["reviewId", "primary_tag"]].to_csv("validation_key.csv", index=False)
print("Tag validation_blind.csv by hand. Do NOT open validation_key.csv until done.")