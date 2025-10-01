import os
import pandas as pd
import streamlit as st
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="HN LLM ETL", page_icon="📰", layout="wide")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("Missing SUPABASE_URL or SUPABASE_KEY in environment.")
else:
    sb = create_client(SUPABASE_URL, SUPABASE_KEY)
    res = sb.table("articles").select("*").order("extracted_at", desc=True).limit(200).execute()
    df = pd.DataFrame(res.data or [])
    st.title("📰 Hacker News — LLM ETL Browser")
    if df.empty:
        st.info("No records yet. Run the collector + structurer + loader.")
    else:
        st.dataframe(df[["id","title","source_url","extracted_at","updated_at"]], use_container_width=True)
        st.subheader("Quick Insights")
        if "source_url" in df.columns:
            dom = df["source_url"].fillna("").str.extract(r"https?://([^/]+)/", expand=False).fillna("(none)")
            counts = dom.value_counts().reset_index()
            counts.columns = ["domain", "count"]
            st.bar_chart(counts.set_index("domain"))
        if "extracted_at" in df.columns:
            day = pd.to_datetime(df["extracted_at"]).dt.date.value_counts().sort_index()
            st.line_chart(day)

