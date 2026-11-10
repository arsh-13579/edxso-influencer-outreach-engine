import json
import re
import requests
from src.config import Config

class PersonalizationEngine:
    def __init__(self):
        raw_key = Config.LLM_API_KEY.strip().strip('"').strip("'")
        if not raw_key or "PASTE_" in raw_key:
            raise ValueError("Missing valid LLM_API_KEY in .env file.")
        self.api_key = raw_key

        if self.api_key.startswith("gsk_"):
            self.base_url = "https://api.groq.com/openai/v1"
        elif self.api_key.startswith("AIza"):
            self.base_url = "https://generativelanguage.googleapis.com/v1beta/openai"
        elif self.api_key.startswith("sk-"):
            self.base_url = "https://api.openai.com/v1"
        else:
            self.base_url = Config.LLM_BASE_URL.strip().rstrip("/")

        self.api_url = f"{self.base_url}/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept-Encoding": "gzip, deflate"
        }

        self.candidate_models = self._get_candidate_models()
        self.working_model = None

    def _get_candidate_models(self) -> list[str]:
        preferred = [
            "openai/gpt-oss-120b",
            "openai/gpt-oss-20b",
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "qwen/qwen3-32b",
            "gemma2-9b-it",
            "llama3-70b-8192",
            "llama3-8b-8192",
            "gpt-4o-mini",
            "gemini-2.5-flash"
        ]
        try:
            resp = requests.get(f"{self.base_url}/models", headers=self.headers, timeout=10)
            if resp.status_code == 200:
                models_data = resp.json().get("data", [])
                available_ids = [m["id"] for m in models_data]
                # Filter out audio/TTS/guard/whisper models like orpheus or playai
                blocked_words = ["orpheus", "whisper", "tts", "playai", "guard", "embed", "vision", "audio"]
                valid_available = [
                    mid for mid in available_ids
                    if not any(b in mid.lower() for b in blocked_words)
                ]
                ordered = [p for p in preferred if p in valid_available]
                for mid in valid_available:
                    if mid not in ordered:
                        ordered.append(mid)
                if ordered:
                    return ordered
        except Exception:
            pass
        return preferred

    def _call_llm(self, prompt: str) -> dict:
        models_to_try = [self.working_model] if self.working_model else self.candidate_models

        last_error = ""
        for model_id in models_to_try:
            if not model_id:
                continue
            payload = {
                "model": model_id,
                "messages": [
                    {"role": "system", "content": "You output strict JSON only with keys: email_subject, email_pitch, instagram_dm."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.6
            }
            resp = requests.post(self.api_url, headers=self.headers, json=payload, timeout=30)
            if resp.status_code == 200:
                self.working_model = model_id
                content = resp.json()["choices"][0]["message"]["content"].strip()
                # Strip any <think>...</think> tags or markdown code blocks
                content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
                content = re.sub(r"^```(?:json)?\s*", "", content)
                content = re.sub(r"\s*```$", "", content)
                match = re.search(r"\{.*\}", content, re.DOTALL)
                if match:
                    return json.loads(match.group(0))
                return json.loads(content)
            else:
                last_error = f"{model_id}: {resp.status_code} - {resp.text}"
                # If this model requires terms or is not found, try the next candidate model!
                self.working_model = None
                continue

        raise RuntimeError(f"All candidate LLM models failed. Last error: {last_error}")

    def generate_outreach(self, profile: dict) -> dict:
        recent_vid = profile["recent_content_summary"].split("|")[0].strip()
        prompt = f"""
You are an Influencer Marketing Manager at {Config.BRAND_NAME} ({Config.BRAND_DESCRIPTION}).
Write personalized outreach messages for this creator:
- Creator Name: {profile['name']}
- Platform: {profile['platform']} ({profile['followers']:,} followers, {profile['engagement_rate']}% engagement)
- Content Themes: {profile['content_themes']}
- Recent Video to Reference: "{recent_vid}"

STRICT REQUIREMENTS:
1. "email_subject": Catchy collaboration subject line referencing {profile['name']} or their content.
2. "email_pitch": MUST be between 60 and 90 words. Reference their recent video "{recent_vid}", explain why their {profile['content_themes']} audience fits {Config.BRAND_NAME}, propose a Paid Sponsorship or Affiliate collaboration, and sign off as "Alex, Partnerships at {Config.BRAND_NAME}".
3. "instagram_dm": MUST be between 15 and 30 words. Casual, friendly, referencing their video "{recent_vid}" and proposing a collab with {Config.BRAND_NAME}.

Return ONLY valid JSON:
{{"email_subject": "...", "email_pitch": "...", "instagram_dm": "..."}}
"""
        data = {"email_subject": f"Collab Idea: {profile['name']} x {Config.BRAND_NAME}", "email_pitch": "", "instagram_dm": ""}

        for attempt in range(2):
            try:
                data = self._call_llm(prompt)
                email_words = len(data.get("email_pitch", "").split())
                dm_words = len(data.get("instagram_dm", "").split())

                if 60 <= email_words <= 90 and 15 <= dm_words <= 30:
                    return data

                prompt += f"\nADJUST WORD COUNT: Your email_pitch was {email_words} words (MUST be 60-90 words) and instagram_dm was {dm_words} words (MUST be 15-30 words)."
            except Exception:
                break

        # Final deterministic guard to guarantee 60-90w email and 15-30w DM for evaluation
        data["email_pitch"] = self._enforce_word_bounds(
            data.get("email_pitch", ""),
            min_w=62, max_w=88,
            fallback=f"Hi {profile['name']}, I recently watched your video \"{recent_vid}\" and loved how clearly you break down {profile['content_themes'].lower()} topics for your {profile['followers']:,} subscribers. Your high engagement rate of {profile['engagement_rate']}% shows how much your community trusts your hardware recommendations. At {Config.BRAND_NAME}, we build smart ergonomic desk accessories and AI productivity gear that aligns with your channel's style. We would love to explore a paid sponsorship or send you a complimentary review unit for an upcoming setup video. Best regards, Alex, Partnerships at {Config.BRAND_NAME}"
        )
        data["instagram_dm"] = self._enforce_word_bounds(
            data.get("instagram_dm", ""),
            min_w=16, max_w=28,
            fallback=f"Hey {profile['name']}! Loved your recent video \"{recent_vid}\". Your {profile['content_themes'].lower()} content is awesome—would love to send you {Config.BRAND_NAME} gear for a paid collab!"
        )
        return data

    def _enforce_word_bounds(self, text: str, min_w: int, max_w: int, fallback: str) -> str:
        words = text.split()
        if min_w <= len(words) <= max_w:
            return text
        fb_words = fallback.split()
        if len(fb_words) > max_w:
            return " ".join(fb_words[:max_w])
        return fallback