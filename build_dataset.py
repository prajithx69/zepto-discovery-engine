from google_play_scraper import reviews, Sort
import pandas as pd
import time

APP_ID = "com.zeptoconsumerapp"
TARGET = 3000
BATCH = 200

all_reviews = []
token = None

print("Pulling Zepto Play Store reviews...")

while len(all_reviews) < TARGET:
    batch, token = reviews(
        APP_ID,
        lang="en",
        country="in",
        sort=Sort.NEWEST,
        count=BATCH,
        continuation_token=token,
    )
    if not batch:
        break
    all_reviews.extend(batch)
    print(f"  collected: {len(all_reviews)}")
    time.sleep(1)  # be polite, avoid rate limits
    if token is None:
        break

df = pd.DataFrame(all_reviews)
df = df[["reviewId", "content", "score", "thumbsUpCount", "at"]]
df["source"] = "play_store"

# keep only substantive text
df = df[df["content"].notna()]
df = df[df["content"].str.len() > 20]

df.to_csv("zepto_playstore_reviews.csv", index=False)
print(f"\nSaved {len(df)} substantive reviews to zepto_playstore_reviews.csv")
print(f"Score distribution:\n{df['score'].value_counts().sort_index()}")