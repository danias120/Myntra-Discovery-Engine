"""
Google Play Store Reviews Scraper

Scrapes customer reviews and ratings for Android fashion apps (Myntra, AJIO, Nykaa, Meesho)
via google-play-scraper library or Apify Google Play actor.
Filters specifically for wishlist usage, shopping behavior, sizing, and product selection.
"""

from __future__ import annotations

from typing import Any, Dict, List
from src.ingestion.base_scraper import BaseScraper
from src.ingestion.config import TARGET_APP_IDS
from src.ingestion.apify_helper import apify_helper
from src.utils.logger import get_logger

logger = get_logger("playstore_scraper")


def is_wishlist_shopping_relevant(text: str) -> bool:
    """
    Filters for reviews regarding wishlist usage, product discovery, sizing,
    pricing, and shopping behavior while excluding pure app bugs and delivery tickets.
    """
    t = text.lower()

    # Negative keywords (pure IT/logistics bugs)
    it_bugs = [
        "app crash", "app crashing", "login otp", "cant login", "cannot login",
        "update bug", "app hanging", "delivery boy", "delivery agent rude",
        "refund not credited", "customer care number", "worst app update"
    ]
    if any(k in t for k in it_bugs) and not any(w in t for w in ["wishlist", "size", "fit", "price", "quality", "dress", "kurta", "jeans", "shoes", "cart"]):
        return False

    # Positive keywords (shopping behavior, wishlist, styling, fit, price)
    relevant_signals = [
        "wishlist", "save for later", "saved", "shortlist", "price", "discount",
        "sale", "size", "fit", "quality", "buy", "cart", "purchase", "shopping",
        "clothes", "outfit", "brand", "dress", "kurta", "jeans", "shoes",
        "compare", "stock", "expensive", "options", "variety", "fabric", "material"
    ]
    return any(k in t for k in relevant_signals)


class PlayStoreScraper(BaseScraper):
    """Scrapes Android app reviews for Indian fashion eCommerce apps."""

    def __init__(self):
        super().__init__()
        self.app_targets = TARGET_APP_IDS["playstore"]

    def get_source_name(self) -> str:
        return "playstore"

    def fetch(self) -> List[Dict[str, Any]]:
        """
        Fetches Play Store reviews using google-play-scraper or Apify.
        """
        records: List[Dict[str, Any]] = []

        # Attempt 1: google-play-scraper Python library
        try:
            from google_play_scraper import reviews, Sort
            for app_name, package_name in self.app_targets.items():
                if len(records) >= self.max_results:
                    break

                logger.info(f"Fetching Play Store reviews for {app_name} ({package_name})...")
                self.limiter.acquire()
                result, _ = reviews(
                    package_name,
                    lang="en",
                    country="in",
                    sort=Sort.NEWEST,
                    count=min(200, self.max_results - len(records)),
                )

                for r in result:
                    content = r.get("content", "")
                    if not is_wishlist_shopping_relevant(content):
                        continue

                    score = r.get("score", 0)
                    at = r.get("at")
                    timestamp = at.isoformat() if at else None
                    review_id = r.get("reviewId")

                    rec = self.create_record(
                        text=content,
                        source_url=f"https://play.google.com/store/apps/details?id={package_name}#{review_id}",
                        timestamp=timestamp,
                        metadata={
                            "app_name": app_name,
                            "package_name": package_name,
                            "rating": score,
                            "thumbs_up": r.get("thumbsUpCount", 0),
                        },
                    )
                    if rec:
                        records.append(rec)

            if records:
                return records

        except ImportError:
            logger.debug("google-play-scraper not installed. Trying Apify actor.")

        # Attempt 2: Apify Play Store Reviews actor
        if apify_helper.is_available:
            actor_id = "apify/google-play-scraper"
            for app_name, package_name in self.app_targets.items():
                if len(records) >= self.max_results:
                    break

                run_input = {
                    "appPackageNames": [package_name],
                    "maxReviews": min(100, self.max_results - len(records)),
                    "sort": "NEWEST",
                }

                try:
                    self.limiter.acquire()
                    items = apify_helper.run_actor(actor_id, run_input, timeout_secs=120)
                    for item in items:
                        text = item.get("content") or item.get("text") or ""
                        if not is_wishlist_shopping_relevant(text):
                            continue

                        score = item.get("score") or item.get("rating") or 0
                        timestamp = item.get("date")

                        rec = self.create_record(
                            text=text,
                            source_url=f"https://play.google.com/store/apps/details?id={package_name}",
                            timestamp=timestamp,
                            metadata={
                                "app_name": app_name,
                                "package_name": package_name,
                                "rating": score,
                            },
                        )
                        if rec:
                            records.append(rec)
                except Exception as e:
                    logger.warning(f"Apify Play Store scraper error for {app_name}: {e}")

        return records
