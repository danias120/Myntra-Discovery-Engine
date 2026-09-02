"""
Relevance Filter Module

Implements a 2-tier domain keyword taxonomy filter for fashion wishlist
and eCommerce shopping behavior, with out-of-scope noise exclusion.

Handles Edge Cases: EC-2.17, EC-2.18, EC-2.19, EC-2.20, EC-2.21
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Set, Tuple

from src.utils.logger import get_logger

logger = get_logger("relevance_filter")

# Tier 1: Core Wishlist & Buying Decision Signals (Matches keep immediately)
TIER_1_KEYWORDS: List[str] = [
    "wishlist", "wish list", "save for later", "saved for later", "saved items",
    "shortlist", "cart abandonment", "outfit build", "mix and match",
    "price drop", "price alert", "flash sale", "stock alert", "restock",
    "out of stock", "pre-cart", "buying intent", "hesitation", "impulse buy",
    "cooling-off", "decision fatigue", "clutter", "folder", "collection",
    "mood board", "vision board", "side-by-side", "compare products",
    "comparison", "sitting in my wishlist", "still in my wishlist",
    "added to my wishlist", "couldnt buy this because", "could not buy",
    "wish i could buy", "sticker shock", "budget pacing", "why do you wishlist",
    "wishlist limit", "capping", "1000 items", "cart", "bookmark"
]

# Tier 2: Fashion eCommerce Friction & Decision Factors (Requires >= 2 matches)
TIER_2_KEYWORDS: List[str] = [
    "sizing", "size chart", "size difference", "fit issue", "fabric quality",
    "color mismatch", "see-through", "sheer", "stitched", "material",
    "true to size", "oversized", "undersized", "shrinkage", "unedited photo",
    "customer photo", "try-on", "haul", "influencer", "social validation",
    "second opinion", "screenshot", "share wishlist", "gifting",
    "occasion shopping", "wedding outfit", "festival sale", "eors",
    "big fashion festival", "vip pass", "kurta", "kurti", "lehenga", "saree",
    "dress", "jeans", "sneakers", "jacket", "co-ord", "palazzo", "anarkali",
    "trousers", "chikankari", "bohot tight", "bohot loose", "size issue",
    "fit nahi", "myntra", "ajio", "nykaa", "mango", "zara", "roadster",
    "tokyo talkies", "libas", "biba", "anouk", "vero moda", "puma", "nike",
    "shopping", "order", "discount", "coupon", "brand", "product", "quality",
    "price", "recommend", "app", "experience", "catalog", "delivery"
]

# Pure Out-of-Scope Exclusions (Pure crash tickets, delivery boy complaints, food/travel)
EXCLUDE_PATTERNS: List[str] = [
    "app crash", "screen frozen", "crashes on open", "screen black",
    "force close", "bank otp", "upi failed", "payment gateway timeout",
    "delivery boy was rude", "courier boy attitude", "delivery guy was rude",
    "swiggy", "zomato", "zepto", "blinkit", "uber", "ola", "hotel booking",
    "flight ticket"
]


class RelevanceFilter:
    """Classifies records based on fashion wishlist and eCommerce behavior relevance."""

    def __init__(self):
        self.tier1_re = [re.compile(r"\b" + re.escape(k) + r"\b", re.IGNORECASE) for k in TIER_1_KEYWORDS]
        self.tier2_re = [re.compile(r"\b" + re.escape(k) + r"\b", re.IGNORECASE) for k in TIER_2_KEYWORDS]
        self.exclude_re = [re.compile(r"\b" + re.escape(k) + r"\b", re.IGNORECASE) for k in EXCLUDE_PATTERNS]
        self.stats = {
            "total_evaluated": 0,
            "passed_tier1": 0,
            "passed_tier2": 0,
            "passed_research_exempt": 0,
            "dropped_out_of_scope": 0,
            "dropped_insufficient_signal": 0,
        }

    def is_relevant(
        self, text: str, source_platform: str = "", source_type: str = ""
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Evaluates relevance based on 2-tier taxonomy rules:
        - Surveys and interviews are 100% exempt (EC-2.20).
        - Tier 1 match (>=1) -> Keep (EC-2.19).
        - Tier 2 match (>=2) -> Keep.
        - Exclude match with 0 Tier 1 -> Discard (EC-2.18).
        """
        if not text:
            return False, "empty_text", {}

        # 1. Research Exemption (EC-2.20)
        s_plat = str(source_platform).lower()
        s_type = str(source_type).lower()
        if s_type in ("interview", "survey", "first_party_survey") or s_plat in ("interviews", "surveys", "interview", "survey"):
            return True, "research_data_exempt", {"tier": "exempt"}

        # Check Exclude Patterns (EC-2.18)
        matched_excludes = [k for k, r in zip(EXCLUDE_PATTERNS, self.exclude_re) if r.search(text)]

        # Check Tier 1
        matched_tier1 = [k for k, r in zip(TIER_1_KEYWORDS, self.tier1_re) if r.search(text)]
        if matched_tier1:
            return True, "tier_1_match", {"tier": 1, "matches": matched_tier1, "excludes": matched_excludes}

        # If it matched pure technical/delivery exclusions and had zero Tier 1 signals, drop it (EC-2.18)
        if matched_excludes:
            return False, "out_of_scope_exclusion", {"excludes": matched_excludes}

        # Check Tier 2
        matched_tier2 = [k for k, r in zip(TIER_2_KEYWORDS, self.tier2_re) if r.search(text)]
        if len(matched_tier2) >= 2:
            return True, "tier_2_match", {"tier": 2, "matches": matched_tier2}

        return False, "insufficient_fashion_signal", {"tier2_count": len(matched_tier2)}

    def process_record(self, record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Evaluates and annotates a record with relevance metadata."""
        self.stats["total_evaluated"] += 1
        text = record.get("text", "")
        source_platform = record.get("source_platform", "")
        source_type = record.get("source_type", "")

        is_rel, reason, details = self.is_relevant(text, source_platform, source_type)

        if not is_rel:
            if "out_of_scope" in reason:
                self.stats["dropped_out_of_scope"] += 1
            else:
                self.stats["dropped_insufficient_signal"] += 1
            logger.debug(f"Dropped non-relevant record {record.get('record_id')}: {reason}")
            return None

        if details.get("tier") == "exempt":
            self.stats["passed_research_exempt"] += 1
        elif details.get("tier") == 1:
            self.stats["passed_tier1"] += 1
        elif details.get("tier") == 2:
            self.stats["passed_tier2"] += 1

        clean_rec = dict(record)
        meta = clean_rec.setdefault("metadata", {})
        meta["relevance_checked"] = True
        meta["relevance_reason"] = reason
        return clean_rec

    def get_stats(self) -> Dict[str, Any]:
        """Returns relevance filtering statistics."""
        return self.stats


# Global singleton instance
relevance_filter = RelevanceFilter()
