from google_play_scraper import reviews, Sort

apps = {
    "Blinkit": "com.grofers.customerapp",
    "Zepto": "com.zeptoconsumerapp",
    "Instamart": "in.swiggy.android",  
}

for name, app_id in apps.items():
    result, _ = reviews(
        app_id,
        lang="en",
        country="in",
        sort=Sort.NEWEST,
        count=500,
    )
    with_text = [r for r in result if r["content"] and len(r["content"]) > 20]
    print(f"{name}: pulled {len(result)}, substantive (>20 chars): {len(with_text)}")