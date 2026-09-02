"""
Apple App Store Reviews Scraper

Fetches customer reviews and star ratings for Myntra, AJIO, Nykaa Fashion, and Meesho
via the official Apple iTunes Customer Reviews RSS/JSON API.
Filters specifically for wishlist usage, shopping behavior, sizing, and product selection.
"""

from __future__ import annotations

from typing import Any, Dict, List
import requests

from src.ingestion.base_scraper import BaseScraper
from src.ingestion.config import TARGET_APP_IDS
from src.utils.logger import get_logger

logger = get_logger("appstore_scraper")


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


class AppStoreScraper(BaseScraper):
    """Scrapes iOS app reviews for targeted Indian fashion eCommerce apps."""

    def __init__(self):
        super().__init__()
        self.app_targets = TARGET_APP_IDS["appstore"]

    def get_source_name(self) -> str:
        return "appstore"

    def fetch(self) -> List[Dict[str, Any]]:
        """
        Fetches customer reviews across all targeted fashion apps from iTunes RSS JSON feed.
        """
        records: List[Dict[str, Any]] = []

        for app_name, app_id in self.app_targets.items():
            if len(records) >= self.max_results:
                break

            logger.info(f"Fetching iOS reviews for {app_name} (App ID: {app_id})...")
            for page in range(1, 11):
                if len(records) >= self.max_results:
                    break

                url = f"https://itunes.apple.com/in/rss/customerreviews/page={page}/id={app_id}/sortby=mostrecent/json"
                try:
                    self.limiter.acquire()
                    resp = requests.get(url, timeout=10)
                    if resp.status_code != 200:
                        break

                    data = resp.json()
                    entries = data.get("feed", {}).get("entry", [])
                    if not entries:
                        break

                    for entry in entries:
                        title = entry.get("title", {}).get("label", "")
                        content = entry.get("content", {}).get("label", "")
                        rating_str = entry.get("im:rating", {}).get("label", "0")
                        updated = entry.get("updated", {}).get("label")
                        review_id = entry.get("id", {}).get("label")

                        rating = int(rating_str) if rating_str.isdigit() else 0
                        full_text = f"{title}\n{content}".strip() if title else content

                        # Filter for wishlist and shopping behavior
                        if not is_wishlist_shopping_relevant(full_text):
                            continue

                        rec = self.create_record(
                            text=full_text,
                            source_url=f"https://apps.apple.com/in/app/id{app_id}#{review_id}" if review_id else None,
                            timestamp=updated,
                            metadata={
                                "app_name": app_name,
                                "app_id": app_id,
                                "rating": rating,
                            },
                        )
                        if rec:
                            records.append(rec)

                except Exception as e:
                    logger.debug(f"Error fetching iOS reviews for {app_name} page {page}: {e}")
                    break

        return records
