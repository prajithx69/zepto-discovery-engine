import os
import json
import time
import pandas as pd
from dotenv import load_dotenv
load_dotenv()

import anthropic

client = anthropic.Anthropic()

MODEL = "claude-haiku-4-5"
BATCH_SIZE = 15
SAMPLE_MODE = False  # True = first 100 reviews only; flip to False for full run

SYSTEM_PROMPT = """You are a qualitative research coder analyzing user feedback about Zepto, an Indian quick-commerce app. Your job is to tag each review against a fixed schema, exactly and consistently.

TAGS (assign one primary_tag, and optionally one secondary_tag):
- HABIT_AUTOPILOT: repeat purchasing, same-basket loyalty, reorder patterns, routine buying
- MENTAL_MODEL: user frames Zepto as only for emergencies/instant needs/staples; planned purchases belong elsewhere (offline, Amazon, Nykaa etc.)
- TRUST_QUALITY: fears or bad experiences with quality/freshness (rotten fruit, stale items, damaged goods)
- TRUST_AUTHENTICITY: fears or claims of fake/counterfeit products (beauty, electronics)
- PRICE_VALUE: price comparisons, better deals elsewhere, discount-driven purchases, deal-triggered category trying
- DISCOVERY_GAP: unaware Zepto sells a category, can't find products, browsing/search friction
- INFO_GAP: wants more product information, reviews, comparisons before buying something new
- SERVICE_NOISE: delivery, refund, support, app-bug complaints with NO category-behavior signal

RULES:
- Tag ONLY from evidence in the text. Do not infer beyond what is written.
- SERVICE_NOISE is the correct tag for pure service rants. Do not force category tags onto them.
- categories_mentioned: list product categories explicitly named (e.g. fruits, vegetables, milk, snacks, skincare, electronics, pet, baby, household, medicines). Empty list if none.
- explored_new: true ONLY if the user describes actually trying a category that was new to them, else false.
- sentiment: positive, negative, or mixed.
- - Generic praise or satisfaction with no described behavior (e.g. "great app", "fast delivery, love it") is SERVICE_NOISE with sentiment positive. HABIT_AUTOPILOT requires evidence of repeat/routine purchasing. PRICE_VALUE requires actual price reasoning or comparison, not just the word "cheap" or "best rate".

OUTPUT: strict JSON array, one object per review, no prose, no markdown fences:
[{"id": "<review id>", "primary_tag": "...", "secondary_tag": "..." or null, "categories_mentioned": [...], "explored_new": true/false, "sentiment": "..."}]"""


def tag_batch(batch_df):
    reviews_block = "\n\n".join(
        f"ID: {row.reviewId}\nREVIEW: {str(row.content)[:600]}"
        for row in batch_df.itertuples()
    )
    response = client.messages.create(
        model=MODEL,
        max_tokens=2500,
        temperature=0,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"Tag these reviews:\n\n{reviews_block}"}],
    )
    text = response.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("```")[1].replace("json", "", 1).strip()
    return json.loads(text)


# load and combine both sources
play = pd.read_csv("zepto_playstore_reviews.csv")
reddit = pd.read_csv("zepto_reddit.csv")
df = pd.concat([play, reddit], ignore_index=True)

if SAMPLE_MODE:
    df = df.head(100)
    print("SAMPLE MODE: tagging first 100 reviews only")

print(f"Tagging {len(df)} reviews in batches of {BATCH_SIZE}...")

all_tags = []
failed_batches = 0

for start in range(0, len(df), BATCH_SIZE):
    batch = df.iloc[start:start + BATCH_SIZE]
    try:
        tags = tag_batch(batch)
        all_tags.extend(tags)
        print(f"  tagged {min(start + BATCH_SIZE, len(df))}/{len(df)}")
    except Exception as e:
        failed_batches += 1
        print(f"  BATCH FAILED at {start}: {type(e).__name__}: {e}")
        if failed_batches >= 3:
            print("Too many failures, stopping to protect credits.")
            break
    time.sleep(1)

tags_df = pd.DataFrame(all_tags)
merged = df.merge(tags_df, left_on="reviewId", right_on="id", how="inner")
out = "tagged_sample.csv" if SAMPLE_MODE else "tagged_full.csv"
merged.to_csv(out, index=False)

print(f"\nSaved {len(merged)} tagged reviews to {out}")
print("\nPrimary tag distribution:")
print(merged["primary_tag"].value_counts())