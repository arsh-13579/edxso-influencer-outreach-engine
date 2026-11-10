import streamlit as st
import pandas as pd
import sqlite3
import os
from src.database import DB_PATH

st.set_page_config(page_title="EDXSO Micro-Influencer Engine", layout="wide")
st.title("🚀 Automated Micro-Influencer Discovery & Outreach Engine")

if not os.path.exists(DB_PATH):
    st.warning("No database found yet! Please run `python main.py` in your terminal first.")
    st.stop()

conn = sqlite3.connect(DB_PATH)
df = pd.read_sql_query("SELECT * FROM influencers", conn)
conn.close()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Discovered", len(df))
col2.metric("Shortlisted (Passed)", len(df[df["filter_status"] == "PASSED"]))
col3.metric("Verified Emails Found", len(df[df["email"] != "Not Found"]))
col4.metric("Outreach Processed", len(df[df["outreach_status"] != "Pending"]))

tab1, tab2, tab3 = st.tabs(["📊 50+ Influencer Dataset & Filtering", "✉️ AI Personalized Outreach", "📬 Outreach Tracker"])

with tab1:
    st.subheader("Discovered Influencers & Classification Reasons")
    st.dataframe(df[["name", "platform", "followers", "engagement_rate", "niche", "email", "filter_status", "filter_reason", "profile_url"]], use_container_width=True)

with tab2:
    st.subheader("Generated Email Pitches (60-90 words) & Instagram DMs (15-30 words)")
    passed_df = df[df["filter_status"] == "PASSED"]
    for _, row in passed_df.iterrows():
        with st.expander(f"🎯 {row['name']} ({row['followers']:,} subs | {row['engagement_rate']}% ER | Email: {row['email']})"):
            st.markdown(f"**Recent Videos Analyzed:** `{row['recent_content_summary']}`")
            st.markdown(f"**Subject:** {row['email_subject']}")
            st.info(f"**Email Pitch ({len(str(row['email_pitch']).split())} words):**\n\n{row['email_pitch']}")
            st.success(f"**Instagram DM ({len(str(row['instagram_dm']).split())} words):**\n\n{row['instagram_dm']}")

with tab3:
    st.subheader("Outreach Delivery & Deduplication Log")
    st.dataframe(df[df["filter_status"] == "PASSED"][["name", "email", "instagram_url", "outreach_status", "sent_date"]], use_container_width=True)
