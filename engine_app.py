import os
import json
import time
import ast
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
load_dotenv()

import anthropic
from google_play_scraper import reviews, Sort

st.set_page_config(page_title="Zepto Category Discovery Engine", layout="wide")

client = anthropic.Anthropic()
MODEL = "claude-haiku-4-5"

SYSTEM_PROMPT = """You are a qualitative research coder analyzing user feedback about Zepto, an Indian quick-commerce app. Tag each review against a fixed schema, exactly and consistently.

TAGS (assign one primary_tag):
- HABIT_AUTOPILOT: repeat/routine purchasing, same-basket loyalty
- MENTAL_MODEL: frames Zepto as only for emergencies/instant/staples; planned purchases belong elsewhere
- TRUST_QUALITY: fear or experience of bad quality/freshness
- TRUST_AUTHENTICITY: fear or claim of fake/counterfeit products
- PRICE_VALUE: actual price reasoning, comparisons, discount-driven buying
- DISCOVERY_GAP: unaware Zepto sells a category, can't find products
- INFO_GAP: wants reviews/details before trying something new
- SERVICE_NOISE: delivery/refund/support/app complaints with no category signal; also generic praise

RULES:
- Tag only from evidence in the text.
- Generic praise with no described behavior is SERVICE_NOISE.
- PRICE_VALUE requires price reasoning, not just the word "cheap".
- categories_mentioned: product categories explicitly named. Empty list if none.

OUTPUT: strict JSON array, no prose, no markdown fences:
[{"id": "...", "primary_tag": "...", "categories_mentioned": [...], "sentiment": "positive|negative|mixed"}]"""

ALIASES = {
    "icecream": "ice cream",
    "ice-cream": "ice cream",
    "veggies": "vegetables",
    "veg": "vegetables",
    "vegetable": "vegetables",
    "fruit": "fruits",
    "curd": "dairy",
    "paneer": "dairy",
}

PERISHABLE = {
    "vegetables", "fruits", "milk", "ice cream", "dairy",
    "chicken", "eggs", "meat", "curd", "bread",
}


@st.cache_data
def load_tagged():
    return pd.read_csv("tagged_full.csv")


def tag_batch(batch_df):
    block = "\n\n".join(
        f"ID: {r.reviewId}\nREVIEW: {str(r.content)[:600]}" for r in batch_df.itertuples()
    )
    resp = client.messages.create(
        model=MODEL, max_tokens=2500, temperature=0,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"Tag these reviews:\n\n{block}"}],
    )
    text = resp.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("```")[1].replace("json", "", 1).strip()
    return json.loads(text)


def cats_for(df, tag, mode=None):
    """mode: 'perishable' keeps only perishables, 'nonperishable' drops them."""
    sub = df[df.primary_tag == tag]
    counts = {}
    for c in sub.categories_mentioned.dropna():
        try:
            for item in ast.literal_eval(c):
                key = str(item).strip().lower()
                key = ALIASES.get(key, key)
                counts[key] = counts.get(key, 0) + 1
        except Exception:
            continue
    s = pd.Series(counts, dtype="int64")
    if mode == "perishable":
        s = s[s.index.isin(PERISHABLE)]
    elif mode == "nonperishable":
        s = s[~s.index.isin(PERISHABLE)]
    return s.sort_values(ascending=True).tail(8)


def run_tagging(work_df):
    if len(work_df) == 0:
        st.warning("No usable rows found.")
        return
    st.write(f"Analysing {len(work_df)} reviews...")
    tags = []
    prog = st.progress(0)
    for start in range(0, len(work_df), 15):
        batch = work_df.iloc[start:start + 15]
        try:
            tags.extend(tag_batch(batch))
        except Exception as e:
            st.warning(f"Batch failed: {e}")
        prog.progress(min((start + 15) / max(len(work_df), 1), 1.0))
        time.sleep(1)
    if tags:
        tdf = pd.DataFrame(tags)
        st.success(f"Tagged {len(tdf)} reviews")
        a, b = st.columns([1, 1], gap="large")
        with a:
            st.bar_chart(tdf["primary_tag"].value_counts().sort_values(),
                         horizontal=True, height=260)
        with b:
            st.dataframe(tdf[["primary_tag", "categories_mentioned", "sentiment"]],
                         use_container_width=True, height=280)


df = load_tagged()

with st.sidebar:
    st.markdown("### Zepto Category Discovery Engine")
    st.caption("Growth team · category expansion")
    st.divider()
    st.markdown("**Corpus**")
    st.write("1,644 Play Store reviews\n\n300 Reddit posts and comments")
    st.markdown("**Method**")
    st.write("Claude Haiku, temperature 0, fixed 8-theme schema, batched classification")
    st.markdown("**Validation**")
    st.write("Blind 50-review hand-coding, 72% agreement")
    st.divider()
    st.caption("Analysis snapshot: 20 July 2026. Live fetch pulls current reviews on demand.")
    st.caption("Built for clarity over decoration. Every number traces to its source data.")

st.title("Why Zepto users don't explore new categories")
st.write(
    "Quick-commerce users settle into repeat baskets. This engine analyses public user "
    "feedback at scale to find what actually blocks category exploration, and validates "
    "those findings against human coding."
)

tab1, tab2, tab3 = st.tabs(["Overview", "Insights", "Method and validation"])

with tab1:
    st.subheader("At a glance")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Reviews analysed", "1,944")
    c2.metric("Sources", "2", help="Play Store and Reddit")
    c3.metric("Themes", "8")
    c4.metric("AI-human agreement", "72%", help="Blind 50-review sample")

    st.divider()

    st.subheader("Where the signal is")
    signal = df[df.primary_tag != "SERVICE_NOISE"]
    st.bar_chart(signal["primary_tag"].value_counts().sort_values(),
                 horizontal=True, height=260)
    st.caption(
        f"{len(df) - len(signal)} of {len(df)} reviews are service complaints carrying no "
        f"category signal. Quality and trust dominate what remains. "
        f"Bars show number of reviews per theme."
    )

    st.divider()

    st.subheader("Two different fears, in two different sets of categories")

    fresh_data = cats_for(df, "TRUST_QUALITY", mode="perishable")
    auth_data = cats_for(df, "TRUST_AUTHENTICITY", mode="nonperishable")

    fresh, auth = st.columns(2, gap="large")

    with fresh:
        st.caption("**Freshness risk** — users fear the product will arrive bad")
        st.bar_chart(fresh_data, horizontal=True, height=280)
        st.caption(
            f"Reviews mentioning each category. {int(fresh_data.sum())} mentions across "
            f"perishable and cold-chain items."
        )

    with auth:
        st.caption("**Authenticity risk** — users fear the product will be fake")
        st.bar_chart(auth_data, horizontal=True, height=280)
        st.caption(
            f"Reviews mentioning each category. Only {int(auth_data.sum())} mentions total, "
            f"so this is directional rather than statistically robust. Note the axis scale "
            f"differs from the chart on the left."
        )

    st.divider()

    st.subheader("Run the pipeline yourself")
    st.write("Three ways to test the workflow: fetch live reviews, upload a CSV, or paste your own text.")

    m1, m2, m3 = st.tabs(["Live fetch", "Upload CSV", "Paste text"])

    with m1:
        st.caption("Scrapes the latest Zepto reviews from the Play Store and tags them now.")
        n = st.select_slider("Reviews to fetch", options=[30, 60, 90, 120], value=60)
        if st.button("Fetch and analyse", key="live"):
            with st.spinner("Fetching from Play Store..."):
                result, _ = reviews("com.zeptoconsumerapp", lang="en", country="in",
                                    sort=Sort.NEWEST, count=n)
                live = pd.DataFrame(result)
                live = live[live["content"].notna()]
                live = live[live["content"].str.len() > 20]
            run_tagging(live)

    with m2:
        st.caption("Upload any CSV with a text column. Works with reviews from any source.")
        up = st.file_uploader("CSV file", type="csv")
        if up is not None:
            udf = pd.read_csv(up)
            col = st.selectbox("Which column holds the review text?", udf.columns)
            if st.button("Analyse uploaded file", key="csv"):
                work = pd.DataFrame({
                    "reviewId": [f"up_{i}" for i in range(len(udf))],
                    "content": udf[col].astype(str),
                })
                work = work[work["content"].str.len() > 20].head(60)
                run_tagging(work)

    with m3:
        st.caption("Paste reviews, one per line.")
        pasted = st.text_area("Reviews", height=160, label_visibility="collapsed")
        if st.button("Analyse pasted text", key="paste"):
            lines = [l.strip() for l in pasted.split("\n") if len(l.strip()) > 20][:30]
            if not lines:
                st.warning("Paste at least one review longer than 20 characters.")
            else:
                run_tagging(pd.DataFrame({
                    "reviewId": [f"own_{i}" for i in range(len(lines))],
                    "content": lines,
                }))

with tab2:
    st.subheader("What the analysis found")

    st.markdown("**1. Most review noise hides a narrow band of real signal**")
    st.write(
        "1,405 of 1,944 reviews are service complaints with no category signal. "
        "The remaining 539 carry the behavioural evidence, and TRUST_QUALITY alone accounts "
        "for 341 of them, roughly 65% of all non-noise signal."
    )

    st.markdown("**2. Distrust is category-specific, and comes in two distinct flavours**")
    st.write(
        "Freshness risk clusters in perishables: vegetables, milk, fruits, ice cream, dairy. "
        "Authenticity risk clusters elsewhere: electronics, skincare, beauty. "
        "Different categories, different fears, different fixes."
    )

    st.markdown("**3. Different sources reveal different truths**")
    st.write(
        "Reddit is 15% of the corpus but carries 56% of MENTAL_MODEL and 63% of "
        "TRUST_AUTHENTICITY tags. App store reviewers report what went wrong; people in "
        "conversation explain how they think. Neither source alone answers the question."
    )

    st.markdown("**4. Interviews reframed the variable**")
    st.write(
        "Six user interviews showed the barrier is not the category itself but whether the "
        "user can verify quality before buying and get recourse after. Loose produce fails "
        "the first test. Electronics without exchange fail the second. Branded, sealed goods "
        "pass both, which is why brand kept surfacing as the unlock."
    )

    st.divider()
    st.subheader("From root cause to opportunity")

    o1, o2 = st.columns(2, gap="large")
    with o1:
        st.markdown("**Freshness risk in perishables**")
        st.caption("341 reviews · vegetables, milk, fruits, ice cream")
        st.write("Root cause: buying online removes the physical inspection users rely on.")
        st.write("Opportunity: supply inspection proxies, or lean on brand and packaging as substitutes.")
    with o2:
        st.markdown("**Authenticity and recourse risk**")
        st.caption("24 reviews · electronics, skincare, beauty")
        st.write("Root cause: users cannot judge authenticity, and fear being stuck with a bad item.")
        st.write("Opportunity: brand-led entry plus a visible first-try guarantee.")

with tab3:
    st.subheader("How the pipeline works")
    st.write(
        "1. **Collect** — Play Store reviews via google-play-scraper (1,644 substantive), "
        "plus 300 Reddit posts and comments from 8 category-relevant threads.\n\n"
        "2. **Classify** — each item tagged by Claude Haiku against a fixed 8-theme schema "
        "at temperature 0, in batches of 15, returning structured JSON.\n\n"
        "3. **Normalise** — category strings are lowercased and mapped through an alias table "
        "so variants such as \"icecream\" and \"ice cream\" are not counted separately.\n\n"
        "4. **Aggregate** — findings are computed from tag counts, not from re-reading the "
        "corpus, so the same input produces the same output.\n\n"
        "5. **Validate** — a blind 50-review sample hand-coded against the same schema, "
        "then compared to the model's tags."
    )

    st.divider()
    st.subheader("Validation: 72% agreement on a blind sample")
    st.write(
        "50 reviews were sampled at random, stripped of AI tags, and hand-coded before the "
        "answer key was opened. Agreement was 36 of 50."
    )
    st.write("**Where the 28% disagreement sits:**")
    st.write(
        "- **Price mention vs price reasoning.** The model tagged generic praise such as "
        "\"products at their lowest price\" as PRICE_VALUE where a human read it as noise. "
        "This inflates a secondary theme without affecting the primary finding.\n"
        "- **Mixed quality-and-service reviews.** Where a review contains both a rotten item "
        "and a refund complaint, primary-tag assignment is genuinely ambiguous to a human "
        "coder too. Disagreements here ran in both directions."
    )
    st.info(
        "Disagreements did not cluster inside TRUST_QUALITY, the theme carrying the headline "
        "finding, so further prompt calibration was deprioritised in favour of primary research."
    )

    st.divider()
    st.subheader("AI risk and mitigation")
    st.write(
        "**Hallucination and mis-classification.** Manual review found the model had tagged an "
        "embedded Reddit advertisement as a genuine user crossing story. Human validation "
        "caught it; an unvalidated pipeline would have carried it into the findings.\n\n"
        "**Probabilistic output.** Re-running a generative summary produces different results "
        "each time. Mitigated by classifying into a fixed schema at temperature 0 and computing "
        "insights from tag counts, so aggregates are stable and reproducible.\n\n"
        "**Free-text category drift.** The model returns category names as free text, which "
        "produced near-duplicate labels. Mitigated with an alias table applied before counting, "
        "and flagged here because the raw output cannot be trusted to be consistent.\n\n"
        "**Source bias.** The corpus skews heavily negative, because people review when angry "
        "or delighted, rarely when satisfied. Review data indicates direction; interviews "
        "supply confidence in that direction.\n\n"
        "**Scope of automation.** In the proposed solution, the model selects the brand bridge, "
        "target category, product and explanation. It is deliberately not given control of "
        "discount depth, because a conversion-optimising system will over-discount to hit its "
        "target. Pricing stays rule-based within per-lever bands enforced in code."
    )