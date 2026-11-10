import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")
    LLM_API_KEY = os.getenv("LLM_API_KEY", "")
    LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1")
    LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
    
    DRY_RUN_SEND = os.getenv("DRY_RUN_SEND", "true").lower() == "true"
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
    SMTP_EMAIL = os.getenv("SMTP_EMAIL", "")
    SMTP_APP_PASSWORD = os.getenv("SMTP_APP_PASSWORD", "")

    BRAND_NAME = "NovaDesk AI"
    BRAND_DESCRIPTION = "Smart ergonomic desk accessories & AI productivity hardware"
    CAMPAIGN_NICHE = "Technology & Desk Setup"
    SEARCH_QUERIES = [
        "desk setup tour",
        "tech productivity gadgets",
        "coding setup aesthetic",
        "macbook accessories review",
        "minimalist tech setup",
        "work from home tech essentials"
    ]

    MIN_FOLLOWERS = 5000
    MAX_FOLLOWERS = 100000
    MIN_ENGAGEMENT_RATE = 1.2
    REQUIRED_KEYWORDS = ["tech", "setup", "desk", "code", "coding", "gadget", "productivity", "review", "mac", "pc", "workspace"]
