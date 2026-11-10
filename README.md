# Automated Micro-Influencer Discovery & Outreach System

An end-to-end AI-powered pipeline built for the **EDXSO AI Engineer Intern Assignment**. This system discovers 50+ real micro-influencers in the **Technology & Desk Setup** niche, evaluates and classifies them against strict quantitative and qualitative criteria, enriches their profiles with contact details, generates strictly length-constrained personalized outreach messages via LLMs, and executes deduplicated outreach tracking.

## 1. Technology Stack & APIs Used
- **Language:** Python 3.11+
- **Discovery API:** YouTube Data API v3 (`google-api-python-client`)
- **Web Scraping & Enrichment:** `requests`, `BeautifulSoup4`, Regular Expressions (Email & Social Handle extraction)
- **AI / LLM Personalization:** OpenAI / Groq API (`gpt-4o-mini` / `llama-3.3-70b-versatile`) + `Pydantic` for structured JSON validation
- **Database & Deduplication:** `SQLite3` (`data/outreach_system.db`) + `Pandas` for CSV reporting
- **Sending Layer:** Python `smtplib` (Gmail SMTP with safe `DRY_RUN` mode)
- **Interactive UI:** `Streamlit` & `Rich` CLI

## 2. System Architecture & Workflow
`Discovery (YouTube API) → Filtering & Classification → Bio & Website Enrichment → LLM Personalization (Self-Correcting Word Count Loop) → Deduplicated Sending Layer → SQLite & CSV Tracker`

### Discovery Methodology
Uses keyword queries (`"desk setup tour"`, `"tech productivity gadgets"`, etc.) via YouTube Data API v3 to fetch 55+ unique creators. For each channel, it retrieves subscriber counts and fetches their 5 most recent uploads to compute a real engagement rate:
$$\text{Engagement Rate (\%)} = \left(\frac{\text{Likes} + \text{Comments}}{\text{Views}}\right) \times 100$$

### Filtering & Classification Logic
A creator is classified as **PASSED** only if all three conditions are met:
1. **Micro-Influencer Tier:** `5,000 <= Followers <= 100,000`
2. **Minimum Engagement:** `Engagement Rate >= 1.2%`
3. **Brand/Content Relevance:** Channel description or recent video titles match target niche keywords (`tech`, `setup`, `desk`, `coding`, `productivity`, `workspace`).
Every failed profile is logged with the exact reason for rejection.

### Profile Enrichment Process
- Extracts business emails directly from channel descriptions using regex.
- Extracts linked Instagram (`instagram.com/...`), TikTok (`tiktok.com/@...`), and personal websites.
- **Fallback Website Crawler:** If no email is listed in the YouTube description, the system automatically visits the creator's external website/portfolio to scrape public contact emails.
- **Zero Fabrication Policy:** Missing emails are explicitly marked as `"Not Found"`.

### AI Personalization & Self-Correcting Word-Count Loop
- Uses structured JSON output containing `email_subject`, `email_pitch`, and `instagram_dm`.
- Dynamically injects the creator's exact recent video titles, follower count, engagement rate, and content themes.
- **Word-Count Enforcement:** A Python validation loop counts the exact words in the LLM output and automatically prompts the model to self-correct if the email pitch is outside **60–90 words** or the Instagram DM is outside **15–30 words**.

### Sending Layer & Duplicate Prevention
- Queries SQLite `outreach_status` before sending to guarantee idempotency (prevents duplicate emails on re-runs).
- Supports live Gmail `SMTP` delivery or safe `DRY_RUN_SEND=true` simulation.
- Profiles with `"Not Found"` emails are automatically routed to `"Manual DM Queue (Email Not Found)"` in compliance with Meta/Instagram platform terms.

## 3. Limitations & Scalability (50 to 500+ Influencers)
- **Current Limitations:** YouTube Data API v3 omits business emails hidden behind interactive reCAPTCHAs on the "About" tab; our pipeline mitigates this by scraping linked external websites. Audience age/gender demographics are not publicly exposed via unauthenticated APIs and are marked accordingly.
- **Scaling to 500+ Influencers:**
  1. Replace synchronous `requests` with `aiohttp` / `asyncio` for concurrent website scraping and LLM calls.
  2. Add Celery + Redis task queues for rate-limited SMTP warming and multi-inbox rotation.
  3. Integrate Apify or Modash APIs to expand cross-platform discovery to Instagram and TikTok natively.

## 4. Setup Instructions
1. Clone the repository and install dependencies:
   ```bash
   pip install -r requirements.txt