import streamlit as st
import pandas as pd

st.title("Zepto Discovery Engine — test")
st.metric("Reviews analyzed", "1,944")
st.metric("AI-human agreement", "72%")

df = pd.read_csv("tagged_full.csv")
st.subheader("Theme distribution")
st.bar_chart(df["primary_tag"].value_counts())