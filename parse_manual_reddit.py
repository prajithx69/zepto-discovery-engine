import os
import pandas as pd

FOLDER = "reddit_manual"
rows = []

for fname in sorted(os.listdir(FOLDER)):
    if not fname.endswith(".txt"):
        continue
    with open(os.path.join(FOLDER, fname), encoding="utf-8") as f:
        text = f.read()

    # split pasted wall of text into chunks by blank lines
    chunks = [c.strip() for c in text.split("\n\n")]

    for i, chunk in enumerate(chunks):
        # keep only human-sounding chunks, drop UI debris
        if len(chunk) < 25:
            continue
        low = chunk.lower()
        if any(x in low for x in ["reply", "share", "report", "upvote", "downvote",
                                   "· ", "ago", "points", "sort by", "view more"]) and len(chunk) < 60:
            continue
        rows.append({
            "reviewId": f"{fname}_{i}",
            "content": chunk,
            "score": None,
            "thumbsUpCount": None,
            "at": None,
            "source": "reddit_manual",
            "thread": fname,
        })

df = pd.DataFrame(rows)
df = df.drop_duplicates(subset="content")
df.to_csv("zepto_reddit.csv", index=False)
print(f"Saved {len(df)} Reddit chunks from {FOLDER}/")