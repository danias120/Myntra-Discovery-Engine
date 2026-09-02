"""
Ingestion Search Query & Platform Configuration

Defines search queries, platform rate limits, target entities, and research data paths.
"""

from __future__ import annotations

from typing import Dict, List
from src.utils.config import INTERVIEWS_DIR, SURVEYS_DIR

# === Search Query Strategy ===
QUERY_TERMS: Dict[str, List[str]] = {
    "primary": [
        "myntra wishlist",
        "myntra shortlist",
        "myntra cart abandon",
        "myntra not buying",
        "myntra save for later",
        "myntra hesitate",
        "online fashion wishlist",
        "fashion shopping cart",
        "ajio wishlist",
        "fashion app wishlist",
        "myntra product review",
        "myntra quality",
    ],
    "extended": [
        "why I don't buy from wishlist",
        "fashion purchase decision",
        "online shopping indecision",
        "saved items never bought",
        "wishlist vs actually buying",
        "fashion try before buy",
        "myntra review",
        "myntra shopping experience",
        "online fashion india",
        "fashion haul india",
        "myntra return policy issue",
        "myntra size fit problem",
    ],
    "myntra_reviews": [
        "https://www.myntra.com",
    ],
}

# Platform-specific search queries and targets
TARGET_SUBREDDITS: List[str] = [
    "india",
    "IndianFashionAddicts",
    "IndianSkincareAddicts",
    "Myntra",
    "TwoXIndia",
]

YOUTUBE_SEARCH_QUERIES: List[str] = [
    "myntra haul",
    "myntra try on",
    "myntra review",
    "ajio haul",
    "myntra wishlist haul",
    "myntra shopping review",
]

INSTAGRAM_HASHTAGS: List[str] = [
    "#myntrahaul",
    "#myntrafashion",
    "#myntrareview",
    "#myntrafinds",
    "#ajiohaul",
]

# App targets for App Store and Google Play Store
TARGET_APP_IDS: Dict[str, Dict[str, str]] = {
    "appstore": {
        "myntra": "907394059",
        "ajio": "1113426206",
        "nykaa_fashion": "1492442531",
        "meesho": "1457958492",
    },
    "playstore": {
        "myntra": "com.myntra.android",
        "ajio": "com.ril.ajio",
        "nykaa_fashion": "com.fsn.nykaafashion",
        "meesho": "com.meesho.supply",
    },
}

# Ingestion Constraints & Targets
RECENCY_MONTHS: int = 12
TARGET_RECORDS_PER_SOURCE: int = 2000

# Platform Rate Limits (Requests per minute & Daily limits)
PLATFORM_RATE_LIMITS: Dict[str, Dict[str, int]] = {
    "reddit": {"requests_per_minute": 10, "daily_limit": 500},
    "quora": {"requests_per_minute": 5, "daily_limit": 200},
    "appstore": {"requests_per_minute": 10, "daily_limit": 500},
    "playstore": {"requests_per_minute": 10, "daily_limit": 500},
    "youtube": {"requests_per_minute": 5, "daily_limit": 300},
    "instagram": {"requests_per_minute": 3, "daily_limit": 200},
    "myntra_reviews": {"requests_per_minute": 5, "daily_limit": 300},
    "forum": {"requests_per_minute": 3, "daily_limit": 100},
}

# First-Party Research Data Paths
RESEARCH_DATA: Dict[str, str] = {
    "interviews_dir": str(INTERVIEWS_DIR),
    "surveys_dir": str(SURVEYS_DIR),
}


def get_query_terms_for_platform(platform: str) -> List[str]:
    """
    Returns the appropriate query list for a given platform.
    """
    platform = platform.lower()
    if platform == "youtube":
        return YOUTUBE_SEARCH_QUERIES
    if platform == "instagram":
        return INSTAGRAM_HASHTAGS
    if platform in ("reddit", "quora", "forum"):
        return QUERY_TERMS["primary"] + QUERY_TERMS["extended"]
    if platform == "myntra_reviews":
        return QUERY_TERMS["myntra_reviews"]
    return QUERY_TERMS["primary"]
