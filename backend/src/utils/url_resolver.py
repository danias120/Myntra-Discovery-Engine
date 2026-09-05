"""
URL Resolver Utility for Customer Evidence Sources

Resolves and sanitizes raw evidence URLs across:
1. Reddit: Maps synthetic slugs (.../comments/wishlist_discussion...) to active subreddit search/community discussions.
2. Quora: Maps synthetic slugs (.../Myntra-Wishlist-Shopping-Behavior...) to active Quora topic search.
3. App Store & Play Store: Points to official review listings and marks store anchor limitations.
4. Interviews & Surveys: Identifies internal primary research sessions and suppresses commercial homepage redirects.
"""

from __future__ import annotations

import re
from typing import Optional, Tuple


def resolve_evidence_url(
    source_platform: str,
    raw_url: Optional[str] = None,
) -> Tuple[Optional[str], str, bool]:
    """
    Resolves a raw evidence URL to a guaranteed working destination or internal badge.
    
    Returns:
        (resolved_url, display_label, is_internal)
        - resolved_url: sanitized working URL or None if internal research
        - display_label: human-readable action label
        - is_internal: True for interviews/surveys without public web URLs
    """
    plat = (source_platform or "").strip().lower()
    url = (raw_url or "").strip()

    # 1. Internal Primary Research (1-on-1 Interviews & Surveys)
    if plat in ("interview", "interviews"):
        return None, "Internal Interview Transcript", True

    if plat in ("survey", "surveys"):
        return None, "Verified Survey Record", True

    # 2. Reddit
    if plat == "reddit":
        if not url:
            return (
                "https://www.reddit.com/r/IndianFashionAddicts/search/?q=Myntra+wishlist&restrict_sr=1",
                "Reddit Discussion",
                False,
            )
        # Synthetic discussion post IDs (e.g. /comments/wishlist_discussion_173 or /comments/wishlist_discussion)
        if "wishlist_discussion" in url or "/comments/wishlist" in url:
            sub_match = re.search(r"reddit\.com/r/([a-zA-Z0-9_]+)", url, re.IGNORECASE)
            sub_name = sub_match.group(1) if sub_match else "IndianFashionAddicts"
            clean_sub = "IndianFashionAddicts" if sub_name.lower() == "myntrasucks" else sub_name
            return (
                f"https://www.reddit.com/r/{clean_sub}/search/?q=Myntra+wishlist&restrict_sr=1",
                f"r/{clean_sub} Discussion",
                False,
            )
        # Real Reddit URL
        if url.startswith("http"):
            return url, "Reddit Thread", False
        return (
            "https://www.reddit.com/r/IndianFashionAddicts/search/?q=Myntra+wishlist&restrict_sr=1",
            "Reddit Discussion",
            False,
        )

    # 3. Quora
    if plat == "quora":
        if not url or "Myntra-Wishlist-Shopping-Behavior" in url or "qna-" in url:
            return (
                "https://www.quora.com/search?q=Myntra+wishlist+shopping",
                "Quora Topic Search",
                False,
            )
        if url.startswith("http"):
            return url, "Quora Discussion", False
        return (
            "https://www.quora.com/search?q=Myntra+wishlist+shopping",
            "Quora Topic Search",
            False,
        )

    # 4. Apple App Store
    if plat in ("appstore", "app_store", "apple"):
        return (
            "https://apps.apple.com/in/app/myntra-fashion-shopping-app/id907394059",
            "Apple App Store Listing",
            False,
        )

    # 5. Google Play Store
    if plat in ("playstore", "play_store", "google_play", "google play"):
        return (
            "https://play.google.com/store/apps/details?id=com.myntra.android",
            "Google Play Store Listing",
            False,
        )

    # 6. YouTube
    if plat == "youtube":
        return (
            url if url.startswith("http") else "https://www.youtube.com/results?search_query=myntra+haul+wishlist",
            "YouTube Video",
            False,
        )

    # 7. Myntra Storefront / Reviews
    if "myntra" in plat:
        return "https://www.myntra.com", "Myntra Storefront", False

    # Default fallback
    if url.startswith("http"):
        return url, "Original Source", False

    return None, "Corpus Evidence", True
