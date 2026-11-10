import re
import requests
from bs4 import BeautifulSoup
from src.config import Config

EMAIL_REGEX = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
IG_REGEX = r"(?:https?:\/\/)?(?:www\.)?instagram\.com\/([a-zA-Z0-9._]+)"
TIKTOK_REGEX = r"(?:https?:\/\/)?(?:www\.)?tiktok\.com\/@([a-zA-Z0-9._]+)"
URL_REGEX = r"https?:\/\/[^\s<>\"']+"

def evaluate_and_enrich(raw_profile: dict) -> dict:
    followers = raw_profile["followers"]
    er = raw_profile["engagement_rate"]
    desc = raw_profile["description"]
    recent_titles = raw_profile["recent_videos"]
    combined_text = f"{raw_profile['name']} {desc} {' '.join(recent_titles)}".lower()

    reasons = []
    passed = True

    if followers < Config.MIN_FOLLOWERS:
        passed = False
        reasons.append(f"Followers ({followers:,}) below minimum ({Config.MIN_FOLLOWERS:,})")
    elif followers > Config.MAX_FOLLOWERS:
        passed = False
        reasons.append(f"Followers ({followers:,}) exceed micro-influencer cap ({Config.MAX_FOLLOWERS:,})")

    if er < Config.MIN_ENGAGEMENT_RATE:
        passed = False
        reasons.append(f"Engagement rate ({er}%) below threshold ({Config.MIN_ENGAGEMENT_RATE}%)")

    matched_keywords = [kw for kw in Config.REQUIRED_KEYWORDS if kw in combined_text]
    if not matched_keywords:
        passed = False
        reasons.append("Low brand/content relevance (no target tech/setup keywords matched)")

    filter_status = "PASSED" if passed else "FAILED"
    filter_reason = (
        f"Matched micro-influencer criteria & keywords: {', '.join(matched_keywords[:4])}"
        if passed else "; ".join(reasons)
    )

    email = extract_email(desc)
    ig_match = re.search(IG_REGEX, desc)
    tiktok_match = re.search(TIKTOK_REGEX, desc)
    
    instagram_url = f"https://instagram.com/{ig_match.group(1)}" if ig_match else "Not Available"
    tiktok_url = f"https://tiktok.com/@{tiktok_match.group(1)}" if tiktok_match else "Not Available"
    website_url = extract_external_website(desc)

    if email == "Not Found" and website_url != "Not Available":
        email = scrape_email_from_website(website_url)

    content_themes = ", ".join(matched_keywords[:5]).title() if matched_keywords else "General Content"
    recent_summary = " | ".join(recent_titles[:3]) if recent_titles else "No recent uploads"

    return {
        "channel_id": raw_profile["channel_id"],
        "name": raw_profile["name"],
        "platform": raw_profile["platform"],
        "profile_url": raw_profile["profile_url"],
        "followers": followers,
        "engagement_rate": er,
        "niche": Config.CAMPAIGN_NICHE if matched_keywords else "Other",
        "content_themes": content_themes,
        "recent_content_summary": recent_summary,
        "email": email,
        "instagram_url": instagram_url,
        "tiktok_url": tiktok_url,
        "website_url": website_url,
        "country": raw_profile["country"],
        "audience_age": "18-34 (Estimated via Niche)",
        "audience_gender": "Not Publicly Available",
        "filter_status": filter_status,
        "filter_reason": filter_reason
    }

def extract_email(text: str) -> str:
    matches = re.findall(EMAIL_REGEX, text)
    valid = [m for m in matches if not m.lower().endswith((".png", ".jpg", ".gif", "sentry.io", "example.com"))]
    return valid[0] if valid else "Not Found"

def extract_external_website(text: str) -> str:
    urls = re.findall(URL_REGEX, text)
    ignored = ["youtube.com", "youtu.be", "instagram.com", "tiktok.com", "twitter.com", "x.com", "facebook.com", "amzn.to", "bit.ly"]
    for u in urls:
        if not any(domain in u.lower() for domain in ignored):
            return u.rstrip(".,)")
    return "Not Available"

def scrape_email_from_website(url: str) -> str:
    try:
        resp = requests.get(url, timeout=4, headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            return extract_email(soup.get_text())
    except Exception:
        pass
    return "Not Found"
