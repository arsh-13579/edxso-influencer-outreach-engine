import sqlite3
import pandas as pd
import os
from datetime import datetime, timezone

DB_PATH = "data/outreach_system.db"

def init_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS influencers (
        channel_id TEXT PRIMARY KEY,
        name TEXT,
        platform TEXT,
        profile_url TEXT,
        followers INTEGER,
        engagement_rate REAL,
        niche TEXT,
        content_themes TEXT,
        recent_content_summary TEXT,
        email TEXT,
        instagram_url TEXT,
        tiktok_url TEXT,
        website_url TEXT,
        country TEXT,
        audience_age TEXT,
        audience_gender TEXT,
        filter_status TEXT,
        filter_reason TEXT,
        email_subject TEXT,
        email_pitch TEXT,
        instagram_dm TEXT,
        outreach_status TEXT DEFAULT 'Pending',
        sent_date TEXT
    )
    """)
    conn.commit()
    conn.close()

def upsert_influencer(data: dict):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO influencers (
        channel_id, name, platform, profile_url, followers, engagement_rate,
        niche, content_themes, recent_content_summary, email, instagram_url,
        tiktok_url, website_url, country, audience_age, audience_gender,
        filter_status, filter_reason
    ) VALUES (
        :channel_id, :name, :platform, :profile_url, :followers, :engagement_rate,
        :niche, :content_themes, :recent_content_summary, :email, :instagram_url,
        :tiktok_url, :website_url, :country, :audience_age, :audience_gender,
        :filter_status, :filter_reason
    )
    ON CONFLICT(channel_id) DO UPDATE SET
        followers=excluded.followers,
        engagement_rate=excluded.engagement_rate,
        email=excluded.email,
        filter_status=excluded.filter_status,
        filter_reason=excluded.filter_reason
    """, data)
    conn.commit()
    conn.close()

def update_messages(channel_id: str, subject: str, email_pitch: str, instagram_dm: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE influencers
    SET email_subject = ?, email_pitch = ?, instagram_dm = ?
    WHERE channel_id = ?
    """, (subject, email_pitch, instagram_dm, channel_id))
    conn.commit()
    conn.close()

def log_outreach(channel_id: str, status: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    cursor.execute("""
    UPDATE influencers
    SET outreach_status = ?, sent_date = ?
    WHERE channel_id = ?
    """, (status, now_str, channel_id))
    conn.commit()
    conn.close()

def export_submission_datasets():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM influencers", conn)
    conn.close()

    dataset_df = df[[
        "name", "platform", "followers", "engagement_rate", "niche",
        "email", "profile_url", "content_themes", "filter_status", "filter_reason"
    ]].rename(columns={
        "name": "Name", "platform": "Platform", "followers": "Followers",
        "engagement_rate": "Engagement (%)", "niche": "Niche", "email": "Email",
        "profile_url": "Profile URL", "content_themes": "Content Theme",
        "filter_status": "Status", "filter_reason": "Classification Reason"
    })
    dataset_df.to_csv("data/discovered_influencers.csv", index=False)

    shortlist_df = df[df["filter_status"] == "PASSED"]
    shortlist_df.to_csv("data/enriched_shortlist.csv", index=False)

    messages_df = df[df["email_pitch"].notna()][[
        "name", "email", "instagram_url", "email_subject", "email_pitch", "instagram_dm"
    ]]
    messages_df.to_csv("data/personalized_messages.csv", index=False)

    tracker_df = df[df["filter_status"] == "PASSED"].copy()
    tracker_df["Message Generated"] = tracker_df["email_pitch"].apply(lambda x: "Yes" if pd.notna(x) and x != "" else "No")
    tracker_df["Sent"] = tracker_df["outreach_status"].apply(lambda x: "Yes" if "Sent" in str(x) else "No")
    tracker_export = tracker_df[[
        "name", "email", "Message Generated", "Sent", "sent_date", "outreach_status"
    ]].rename(columns={
        "name": "Influencer", "email": "Email", "sent_date": "Date", "outreach_status": "Status"
    })
    tracker_export.to_csv("data/outreach_tracker.csv", index=False)
