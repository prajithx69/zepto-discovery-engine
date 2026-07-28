from app_store_web_scraper import AppStoreEntry
import pandas as pd

app = AppStoreEntry(app_id=1575323645, country="in")  # Zepto: Groceries in minutes (India)

rows = []
for r in app.reviews(limit=400):
    if r.content and len(r.content) > 20:
        rows.append({
            "reviewId": f"ios_{r.id}",
            "content": r.content,
            "score": r.rating,
            "thumbsUpCount": None,
            "at": r.date,
            "source": "app_store",
        })

df = pd.DataFrame(rows)
if len(df) == 0:
    print("Zero reviews pulled. Feed empty or blocked, stop and report.")
else:
    df.to_csv("zepto_appstore_reviews.csv", index=False)
    print(f"Saved {len(df)} App Store reviews")
    print(f"Score distribution:\n{df['score'].value_counts().sort_index()}")