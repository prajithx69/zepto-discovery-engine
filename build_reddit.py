import requests
import pandas as pd
import time

THREADS = [
    "https://www.reddit.com/r/india/comments/1j51dct/zepto_sending_stalerotten_veggies_for_cheap_prices/",
    "https://www.reddit.com/r/IndianFood/comments/1uhrg7m/buying_fruits_from_zepto_is_becoming_a_waste_of/",
    "https://www.reddit.com/r/bangalore/comments/1geprqw/zepto_users_beware/",
    "https://www.reddit.com/r/bangalore/comments/1cm3dkq/my_experience_with_zepto/",
    "https://www.reddit.com/r/mumbai/comments/1ju4axj/zepto_scam_south_mumbai/",
    "https://www.reddit.com/r/IndianBeautyDeals/comments/1tws6ow/bengaluru_people_run_to_zepto/",
    "https://www.reddit.com/r/IndianBeautyDeals/comments/1r5a20b/products_on_zepto/",
    "https://www.reddit.com/r/IndianBeautyDeals/comments/1tyoy9u/zepto/",
    "https://www.reddit.com/r/IndianSkincareAddicts/comments/1goyn91/beware_zepto_selling_fake_beauty_care_products/",
    "https://www.reddit.com/r/delhi/comments/1mqkkkd/never_buy_any_electronics_from_zepto/",
    "https://www.reddit.com/r/IndiaTech/comments/1nw43k8/expensive_electronics_from_zepto/",
    "https://www.reddit.com/r/GadgetsIndia/comments/1ic2wsu/is_it_safe_to_buy_electronics_from_zepto/",
    "https://www.reddit.com/r/FuckZepto/comments/1qfzhgl/why_do_people_even_order_from_zepto_anymore/",
    "https://www.reddit.com/r/SurveyExchangeIndia/comments/1sc32xi/quick_3min_survey_on_grocery_app_reordering/",
    "https://www.reddit.com/r/hyderabad/comments/1liaxw8/did_hyd_really_say_f_you_zepto/",
    "https://www.reddit.com/r/hyderabad/comments/1ijwzd8/zepto_does_the_most_psycho_shit_i_swear/",
    "https://www.reddit.com/r/delhi/comments/1hjdsvh/zepto_sellers_getting_worse/",
    "https://www.reddit.com/r/delhi/comments/1i2hlh9/zepto_scam_strikes_again/",
    "https://www.reddit.com/r/delhi/comments/1maqkr7/what_is_this_behaviour_zepto/",
    "https://www.reddit.com/r/delhi/comments/1kdkuio/zepto_is_a_scam/",
    "https://www.reddit.com/r/Fitness_India/comments/1jh4qkj/never_buy_anything_from_zepto/",
    "https://www.reddit.com/r/Newsandviewsindia/comments/1k4wk0m/zomato_swiggy_zepto_is_quick_commerce_the_next/",
]

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) grad-research-project/1.0"}

rows = []


def walk_comments(children, thread_url):
    """Recursively collect all comments and replies from a thread."""
    for c in children:
        if c.get("kind") != "t1":
            continue
        d = c["data"]
        body = d.get("body", "")
        if body and len(body) > 20 and body not in ("[deleted]", "[removed]"):
            rows.append({
                "reviewId": d.get("id"),
                "content": body,
                "score": None,
                "thumbsUpCount": d.get("ups", 0),
                "at": d.get("created_utc"),
                "source": "reddit",
                "thread": thread_url,
            })
        replies = d.get("replies")
        if replies and isinstance(replies, dict):
            walk_comments(replies.get("data", {}).get("children", []), thread_url)


def fetch_thread(url, attempt=1):
    """Fetch one thread's JSON, with one retry on rate limit."""
    json_url = url.rstrip("/") + ".json"
    r = requests.get(json_url, headers=HEADERS, timeout=15)
    if r.status_code == 429 and attempt == 1:
        print("  rate limited, waiting 30s and retrying...")
        time.sleep(30)
        return fetch_thread(url, attempt=2)
    r.raise_for_status()
    return r.json()


success, failed = 0, 0

for url in THREADS:
    short = url.split("/comments/")[1][:45]
    try:
        data = fetch_thread(url)

        # index 0 = the post itself, index 1 = the comment tree
        post = data[0]["data"]["children"][0]["data"]
        post_text = (post.get("title", "") + ". " + post.get("selftext", "")).strip()
        if len(post_text) > 20:
            rows.append({
                "reviewId": post.get("id"),
                "content": post_text,
                "score": None,
                "thumbsUpCount": post.get("ups", 0),
                "at": post.get("created_utc"),
                "source": "reddit",
                "thread": url,
            })

        before = len(rows)
        walk_comments(data[1]["data"]["children"], url)
        got = len(rows) - before + 1
        success += 1
        print(f"ok:     {short}  (+{got}, total {len(rows)})")

    except Exception as e:
        failed += 1
        print(f"FAILED: {short}  ({type(e).__name__}: {e})")

    time.sleep(2)

df = pd.DataFrame(rows)
if len(df) > 0:
    df = df.drop_duplicates(subset="content")
    df.to_csv("zepto_reddit.csv", index=False)

print(f"\nThreads: {success} ok, {failed} failed")
print(f"Saved {len(df)} unique Reddit posts/comments to zepto_reddit.csv")