from googleapiclient.discovery import build
from src.config import Config

class YouTubeDiscovery:
    def __init__(self):
        if not Config.YOUTUBE_API_KEY or "PASTE_" in Config.YOUTUBE_API_KEY:
            raise ValueError("Missing valid YOUTUBE_API_KEY in .env file.")
        self.youtube = build("youtube", "v3", developerKey=Config.YOUTUBE_API_KEY)

    def discover_channels(self, target_count: int = 55) -> list[dict]:
        discovered_channel_ids = set()
        raw_channels = []

        for query in Config.SEARCH_QUERIES:
            if len(discovered_channel_ids) >= target_count:
                break

            search_response = self.youtube.search().list(
                q=query,
                type="video",
                part="snippet",
                maxResults=25,
                relevanceLanguage="en"
            ).execute()

            batch_ids = []
            for item in search_response.get("items", []):
                cid = item["snippet"]["channelId"]
                if cid not in discovered_channel_ids:
                    discovered_channel_ids.add(cid)
                    batch_ids.append(cid)

            if batch_ids:
                channels_data = self._fetch_channel_details(batch_ids)
                raw_channels.extend(channels_data)

        return raw_channels[:target_count]

    def _fetch_channel_details(self, channel_ids: list[str]) -> list[dict]:
        response = self.youtube.channels().list(
            id=",".join(channel_ids),
            part="snippet,statistics,contentDetails"
        ).execute()

        results = []
        for item in response.get("items", []):
            stats = item.get("statistics", {})
            snippet = item.get("snippet", {})
            uploads_playlist = item.get("contentDetails", {}).get("relatedPlaylists", {}).get("uploads")

            subs = int(stats.get("subscriberCount", 0))
            recent_videos, engagement_rate = self._analyze_recent_videos(uploads_playlist, subs)

            custom_url = snippet.get("customUrl", f"channel/{item['id']}")
            profile_url = f"https://www.youtube.com/{custom_url}"

            results.append({
                "channel_id": item["id"],
                "name": snippet.get("title", "Unknown"),
                "platform": "YouTube",
                "profile_url": profile_url,
                "description": snippet.get("description", ""),
                "country": snippet.get("country", "Not Available"),
                "followers": subs,
                "engagement_rate": round(engagement_rate, 2),
                "recent_videos": recent_videos
            })
        return results

    def _analyze_recent_videos(self, playlist_id: str, followers: int) -> tuple[list[str], float]:
        if not playlist_id or followers == 0:
            return [], 0.0
        try:
            pl_resp = self.youtube.playlistItems().list(
                playlistId=playlist_id,
                part="contentDetails",
                maxResults=5
            ).execute()
            video_ids = [item["contentDetails"]["videoId"] for item in pl_resp.get("items", [])]
            if not video_ids:
                return [], 0.0

            vid_resp = self.youtube.videos().list(
                id=",".join(video_ids),
                part="snippet,statistics"
            ).execute()

            titles = []
            total_interactions = 0
            total_views = 0

            for v in vid_resp.get("items", []):
                titles.append(v["snippet"]["title"])
                v_stats = v.get("statistics", {})
                views = int(v_stats.get("viewCount", 0))
                likes = int(v_stats.get("likeCount", 0))
                comments = int(v_stats.get("commentCount", 0))
                total_views += views
                total_interactions += (likes + comments)

            er = (total_interactions / total_views) * 100 if total_views > 0 else 0.0
            return titles, er
        except Exception:
            return [], 0.0
