"""
YouTube Comments Scraper

Scrapes public comments from fashion haul, try-on, and review videos.
Primary: YouTube Data API v3 (free tier: 10,000 quota units/day)
Fallback: Apify YouTube Scraper actor (streamers/youtube-scraper)
"""

from __future__ import annotations

from typing import Any, Dict, List
from src.ingestion.base_scraper import BaseScraper
from src.ingestion.config import YOUTUBE_SEARCH_QUERIES
from src.ingestion.apify_helper import apify_helper
from src.utils.config import YOUTUBE_API_KEY
from src.utils.logger import get_logger

logger = get_logger("youtube_scraper")


class YouTubeScraper(BaseScraper):
    """Scrapes comments and feedback from fashion review/haul YouTube videos."""

    def __init__(self):
        super().__init__()
        self.search_queries = YOUTUBE_SEARCH_QUERIES
        self.api_key = YOUTUBE_API_KEY

    def get_source_name(self) -> str:
        return "youtube"

    def fetch(self) -> List[Dict[str, Any]]:
        """
        Fetches comments using YouTube Data API v3 as primary, or Apify fallback.
        """
        records: List[Dict[str, Any]] = []

        # Attempt 1: YouTube Data API v3
        if self.api_key:
            try:
                records = self._fetch_via_data_api()
                if records:
                    return records
            except Exception as e:
                logger.warning(f"YouTube Data API v3 failed: {e}. Attempting Apify fallback.")

        # Attempt 2: Apify YouTube Scraper Actor
        if apify_helper.is_available:
            records = self._fetch_via_apify()

        return records

    def _fetch_via_data_api(self) -> List[Dict[str, Any]]:
        """Uses google-api-python-client with YouTube Data API v3."""
        from googleapiclient.discovery import build

        records = []
        youtube = build("youtube", "v3", developerKey=self.api_key)

        for query in self.search_queries[:4]:
            if len(records) >= self.max_results:
                break

            self.limiter.acquire()
            # 1. Search for relevant fashion videos
            search_response = (
                youtube.search()
                .list(
                    q=query,
                    part="snippet",
                    maxResults=5,
                    type="video",
                    regionCode="IN",
                    relevanceLanguage="en",
                )
                .execute()
            )

            video_items = search_response.get("items", [])
            for v_item in video_items:
                video_id = v_item.get("id", {}).get("videoId")
                video_title = v_item.get("snippet", {}).get("title", "")
                if not video_id:
                    continue

                # 2. Fetch top comments for this video
                try:
                    self.limiter.acquire()
                    comment_response = (
                        youtube.commentThreads()
                        .list(
                            part="snippet",
                            videoId=video_id,
                            maxResults=20,
                            textFormat="plainText",
                        )
                        .execute()
                    )

                    c_items = comment_response.get("items", [])
                    for c_item in c_items:
                        top_comment = (
                            c_item.get("snippet", {})
                            .get("topLevelComment", {})
                            .get("snippet", {})
                        )
                        comment_text = top_comment.get("textDisplay", "")
                        published_at = top_comment.get("publishedAt")
                        like_count = top_comment.get("likeCount", 0)

                        rec = self.create_record(
                            text=comment_text,
                            source_url=f"https://www.youtube.com/watch?v={video_id}",
                            timestamp=published_at,
                            metadata={
                                "video_title": video_title,
                                "video_id": video_id,
                                "like_count": like_count,
                            },
                        )
                        if rec:
                            records.append(rec)

                except Exception as e:
                    # Comments may be disabled on some videos
                    logger.debug(f"Could not fetch comments for video {video_id}: {e}")
                    continue

        return records

    def _fetch_via_apify(self) -> List[Dict[str, Any]]:
        """Uses streamers/youtube-scraper actor."""
        records = []
        actor_id = "streamers/youtube-scraper"

        run_input = {
            "searchKeywords": self.search_queries[:3],
            "maxComments": min(50, self.max_results),
            "maxResults": 5,
        }

        try:
            self.limiter.acquire()
            items = apify_helper.run_actor(actor_id, run_input, timeout_secs=180)
            for item in items:
                comment_text = item.get("text") or item.get("comment") or ""
                video_url = item.get("videoUrl") or item.get("url")
                video_title = item.get("videoTitle") or item.get("title")

                rec = self.create_record(
                    text=comment_text,
                    source_url=video_url,
                    timestamp=item.get("date"),
                    metadata={
                        "video_title": video_title,
                        "like_count": item.get("likes", 0),
                    },
                )
                if rec:
                    records.append(rec)
        except Exception as e:
            logger.warning(f"Apify YouTube scraper error: {e}")

        return records
