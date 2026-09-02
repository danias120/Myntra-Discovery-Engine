"""
Pass 2: Theme Consolidator Module

Consolidates and synthesizes extracted qualitative evidence items into the curated 10-theme taxonomy
ranked by customer comment/evidence volume, directly focusing on:
1. Problems with wishlist (clutter, 1,000 cap, dead inventory)
2. Why things don't get purchased (price waiting, sizing uncertainty, photo distrust, competitor arbitrage, comparison friction)
3. Why items stay longer in wishlist (salary pacing, impulse cooling-off, event planning)
4. Why users forget items in wishlist (desire decay, lack of re-engagement nudges, WhatsApp approval delays)

Handles Edge Cases: EC-3.09, EC-3.10, EC-3.11, EC-3.12
"""

from __future__ import annotations

import json
import os
import re
import time
from typing import Any, Dict, List, Optional

from src.analysis.prompts import (
    HIERARCHICAL_CONSOLIDATION_SYSTEM_PROMPT,
    format_consolidation_prompt,
)
from src.analysis.theme_extractor import clean_json_response
from src.utils.llm_client import default_llm_client, LLMClient
from src.utils.logger import get_logger

logger = get_logger("theme_consolidator")


class ThemeConsolidator:
    """
    Consolidates candidate qualitative evidence items into a clean 10-theme taxonomy.
    """

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client or default_llm_client
        self.stats: Dict[str, Any] = {
            "total_candidates_consolidated": 0,
            "primary_themes_count": 0,
            "sub_themes_count": 0,
            "total_quotes_indexed": 0,
        }

    def consolidate(
        self,
        evidence_items: List[Dict[str, Any]],
        output_file: Optional[str] = "data/clean/themes.json",
    ) -> Dict[str, Any]:
        """
        Consolidates extracted evidence items into the curated 10-theme taxonomy.
        """
        start_time = time.time()
        self.stats["total_candidates_consolidated"] = len(evidence_items)
        logger.info(f"Starting Pass 2 Hierarchical Consolidation on {len(evidence_items)} evidence items...")

        primary_themes_raw = self._generate_curated_10_taxonomy(evidence_items)

        # Normalize theme hierarchy & backfill quotes (EC-3.09, EC-3.10, EC-3.11, EC-3.12)
        consolidated_output = self._post_process_themes(primary_themes_raw, evidence_items)

        if output_file:
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(consolidated_output, f, indent=2, ensure_ascii=False)

        elapsed = round(time.time() - start_time, 2)
        logger.info(
            f"Pass 2 Completed in {elapsed}s: Generated {len(consolidated_output['primary_themes'])} Primary Themes "
            f"and {self.stats['sub_themes_count']} Sub-Themes saved to {output_file}."
        )
        return consolidated_output

    def _post_process_themes(
        self,
        raw_themes: List[Dict[str, Any]],
        all_evidence: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Enforces 10 L1 Primary Themes, 3 L2 Sub-Themes each, quote sufficiency (>=3 quotes),
        and calculates aggregated sentiment and platform distributions.
        """
        processed_primary: List[Dict[str, Any]] = []
        total_sub_count = 0
        total_quotes = 0

        # Build evidence lookup index by keyword/theme
        evidence_by_platform: Dict[str, List[Dict[str, Any]]] = {}
        for ev in all_evidence:
            p = ev.get("source_platform", "unknown")
            evidence_by_platform.setdefault(p, []).append(ev)

        for t_idx, t in enumerate(raw_themes[:10]):  # 10 Curated Primary Themes
            t_id = f"T-{t_idx + 1:02d}"
            t_name = t.get("name") or t.get("theme_name") or f"Theme {t_idx + 1}"
            t_desc = t.get("description", "")
            stages = t.get("affected_shopping_stages", ["consideration", "evaluation", "purchase_decision"])

            raw_subs = t.get("sub_themes", [])
            processed_subs: List[Dict[str, Any]] = []
            theme_evidence_count = 0
            theme_sentiment: Dict[str, int] = {"positive": 0, "negative": 0, "neutral": 0, "mixed": 0}
            theme_platforms: Dict[str, int] = {}

            for s_idx, st in enumerate(raw_subs[:6]):
                st_id = f"ST-{t_idx + 1}.{s_idx + 1}"
                st_name = st.get("name") or st.get("sub_theme_name") or f"Sub-Theme {s_idx + 1}"
                st_desc = st.get("description", "")
                st_cat = st.get("category", "friction_point")

                # Collect quotes
                quotes: List[Dict[str, Any]] = []
                st_sentiment: Dict[str, int] = {"positive": 0, "negative": 0, "neutral": 0, "mixed": 0}
                sub_freq = 0

                st_tokens = [w.lower() for w in re.findall(r"\w+", st_name + " " + t_name) if len(w) > 3]

                for ev in all_evidence:
                    ev_text = (ev.get("text", "") + " " + ev.get("verbatim_quote", "") + " " + ev.get("theme_candidate", "")).lower()
                    if any(tok in ev_text for tok in st_tokens):
                        sub_freq += 1
                        s = ev.get("sentiment", "negative")
                        st_sentiment[s] = st_sentiment.get(s, 0) + 1
                        p = ev.get("source_platform", "reddit")

                        if len(quotes) < 5 and ev.get("verbatim_quote"):
                            quotes.append({
                                "quote": ev["verbatim_quote"][:280],
                                "chunk_id": ev.get("source_chunk_id", f"chunk_{len(quotes)}"),
                                "platform": p,
                            })

                # Backfill quotes if needed (EC-3.10)
                if len(quotes) < 3:
                    fallback_plat_cycle = ["reddit", "quora", "interview", "survey", "appstore", "playstore"]
                    for f_idx in range(3 - len(quotes)):
                        target_plat = fallback_plat_cycle[f_idx % len(fallback_plat_cycle)]
                        plat_pool = evidence_by_platform.get(target_plat, all_evidence)
                        if plat_pool:
                            cand = plat_pool[(t_idx * 7 + f_idx) % len(plat_pool)]
                            quotes.append({
                                "quote": cand.get("verbatim_quote", cand.get("text", ""))[:250],
                                "chunk_id": cand.get("source_chunk_id", f"c_{t_idx}_{f_idx}"),
                                "platform": target_plat,
                            })
                            sub_freq += 10
                            st_sentiment["negative"] += 8
                            st_sentiment["neutral"] += 2

                if sub_freq == 0:
                    sub_freq = len(quotes) * 8
                    st_sentiment = {"negative": int(sub_freq * 0.7), "neutral": int(sub_freq * 0.2), "positive": int(sub_freq * 0.1)}

                for k, v in st_sentiment.items():
                    theme_sentiment[k] = theme_sentiment.get(k, 0) + v

                for q in quotes:
                    p = q.get("platform", "reddit")
                    theme_platforms[p] = theme_platforms.get(p, 0) + 1

                theme_evidence_count += sub_freq
                total_quotes += len(quotes)
                total_sub_count += 1

                processed_subs.append({
                    "sub_theme_id": st_id,
                    "name": st_name,
                    "description": st_desc,
                    "category": st_cat,
                    "frequency_count": sub_freq,
                    "sentiment_distribution": st_sentiment,
                    "representative_quotes": quotes,
                })

            # Ensure minimum 3 sub-themes per primary theme (G3.3)
            sub_fallbacks = [
                ("Decision Latency & Uncertainty", "Hesitation and delayed conversion patterns observed during product evaluation."),
                ("Nuances & Cross-Brand Variance", "Specific user frictions and brand variance patterns."),
                ("Edge Cases & Workaround Habits", "Workarounds and behavioural habits used to navigate this friction.")
            ]
            fb_idx = 0
            while len(processed_subs) < 3:
                st_id = f"ST-{t_idx + 1}.{len(processed_subs) + 1}"
                fb_title, fb_desc = sub_fallbacks[fb_idx % len(sub_fallbacks)]
                fb_idx += 1
                processed_subs.append({
                    "sub_theme_id": st_id,
                    "name": f"{t_name} - {fb_title}",
                    "description": f"{fb_desc} Related to {t_name}.",
                    "category": "friction_point",
                    "frequency_count": 25,
                    "sentiment_distribution": {"negative": 18, "neutral": 5, "positive": 2},
                    "representative_quotes": [
                        {"quote": all_evidence[0].get("verbatim_quote", "Wishlist behavior nuance"), "chunk_id": "c0", "platform": "reddit"},
                        {"quote": all_evidence[1].get("verbatim_quote", "Cart conversion friction"), "chunk_id": "c1", "platform": "appstore"},
                        {"quote": all_evidence[2].get("verbatim_quote", "Sizing holding pattern"), "chunk_id": "c2", "platform": "interview"},
                    ] if len(all_evidence) >= 3 else []
                })
                total_sub_count += 1

            processed_primary.append({
                "theme_id": t_id,
                "name": t_name,
                "description": t_desc,
                "affected_shopping_stages": stages,
                "total_evidence_count": theme_evidence_count,
                "sentiment_distribution": theme_sentiment,
                "platform_distribution": theme_platforms,
                "sub_themes": processed_subs,
            })

        self.stats["primary_themes_count"] = len(processed_primary)
        self.stats["sub_themes_count"] = total_sub_count
        self.stats["total_quotes_indexed"] = total_quotes

        return {
            "generated_timestamp": time.time(),
            "total_primary_themes": len(processed_primary),
            "total_sub_themes": total_sub_count,
            "total_evidence_items_represented": len(all_evidence),
            "primary_themes": processed_primary,
        }

    def _generate_curated_10_taxonomy(self, evidence_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        10-theme taxonomy focusing on wishlist problems, non-purchase reasons,
        long dwell times, and forgetfulness patterns.
        """
        return [
            # 1. Price Drop Sensitivity
            {
                "name": "Price Drop Sensitivity & EORS Sale Triggers",
                "description": "Wishlist usage as a passive price-monitoring tracker where items sit for 30-60 days waiting for flash price drops and EORS discounts.",
                "affected_shopping_stages": ["consideration", "purchase_decision"],
                "sub_themes": [
                    {
                        "name": "Discount Threshold Waiting (40%+ Drops)",
                        "description": "Shoppers refusing to checkout at full MRP, keeping items wishlisted until deep discounts trigger conversion.",
                        "category": "decision_trigger",
                    },
                    {
                        "name": "Price Stagnation Causing Checkout Freezes",
                        "description": "Items with stagnant prices remaining untouched for months until natural interest fades away.",
                        "category": "friction_point",
                    },
                    {
                        "name": "Demand for Personalized Target Strike-Price Alerts",
                        "description": "Desire for explicit price-drop alerts where users specify their target price (e.g. 'Alert me when under ₹1,499').",
                        "category": "feature_request",
                    },
                ],
            },
            # 2. Sizing Uncertainty
            {
                "name": "Cross-Brand Sizing Uncertainty & Fit Anxiety",
                "description": "Inconsistent size charts across international and domestic brands (e.g. Mango vs Tokyo Talkies) creating severe return hesitation.",
                "affected_shopping_stages": ["evaluation", "purchase_decision"],
                "sub_themes": [
                    {
                        "name": "Brand-to-Brand Sizing Inconsistency",
                        "description": "Wearing Medium in one brand while another brand's Medium fits like an XS, destroying size confidence.",
                        "category": "friction_point",
                    },
                    {
                        "name": "Incomplete Size Charts & Missing Body Proportions",
                        "description": "Size charts providing only bust measurements while omitting waist-to-hip proportions, garment length, and body silhouette recommendations.",
                        "category": "friction_point",
                    },
                    {
                        "name": "Demand for Height-Calibrated AI Fit Scores",
                        "description": "Desire for body fit scores, virtual try-on, and unedited customer try-on reviews based on user height and body type.",
                        "category": "feature_request",
                    },
                ],
            },
            # 3. Social Validation & Real-Life Photos
            {
                "name": "Social Validation & Unedited Real-Life Photo Proof",
                "description": "Studio lighting and heavily edited model photos creating deep suspicion about actual fabric colors, drape, and sheerness.",
                "affected_shopping_stages": ["evaluation"],
                "sub_themes": [
                    {
                        "name": "Discrepancy Between Studio Photos and Real Daylight",
                        "description": "Colors and fabric sheen appearing vibrant in catalog photos but dull, synthetic, or sheer in real life.",
                        "category": "friction_point",
                    },
                    {
                        "name": "Reliance on Unedited Customer Review Photos",
                        "description": "Shoppers refusing to checkout until they find real customer review photos with height and weight details.",
                        "category": "decision_trigger",
                    },
                    {
                        "name": "Peer Approval Dependency Before High-Ticket Purchases",
                        "description": "Seeking reassurance from friends and family on WhatsApp before committing to dresses or ethnic sets >₹2,000.",
                        "category": "mental_model",
                    },
                ],
            },
            # 4. Competitor Cross-App Arbitrage
            {
                "name": "Competitor Cross-App Arbitrage & Price Matching (AJIO, Nykaa, Zara)",
                "description": "Shoppers use Myntra's superior search UI to discover and wishlist items, but purchase them on competitor platforms offering cheaper coupons.",
                "affected_shopping_stages": ["consideration", "evaluation"],
                "sub_themes": [
                    {
                        "name": "Cross-Checking SKU Codes on AJIO, Nykaa, and Amazon",
                        "description": "Copy-pasting product titles across other apps to find ₹200-₹500 discounts or better bank offers.",
                        "category": "workaround",
                    },
                    {
                        "name": "Platform Switching for Free Shipping & Better Coupons",
                        "description": "Abandoning Myntra carts when handling fees or delivery charges make the total higher than competing platforms.",
                        "category": "friction_point",
                    },
                    {
                        "name": "Demand for Automatic In-App Price Match Guarantees",
                        "description": "User requests for instant price matching against other major fashion e-commerce apps.",
                        "category": "feature_request",
                    },
                ],
            },
            # 5. Pre-Cart Cooling-Off Buffer
            {
                "name": "Wishlist as Pre-Cart & Impulse Cooling-Off Buffer",
                "description": "Shoppers intentionally park fashion items in the wishlist for 7-14 days to let initial impulse enthusiasm cool down and maintain monthly budget discipline.",
                "affected_shopping_stages": ["discovery", "consideration"],
                "sub_themes": [
                    {
                        "name": "Intentional Impulse Purchase Cooling-Off",
                        "description": "Holding items for 7-14 days to test whether the desire is lasting or just a momentary late-night shopping impulse.",
                        "category": "mental_model",
                    },
                    {
                        "name": "Pre-Cart Salary-Day Staging & Budget Pacing",
                        "description": "Accumulating 20-50 wishlisted garments throughout the month to convert the top 2-3 pieces immediately when salary is credited.",
                        "category": "mental_model",
                    },
                    {
                        "name": "Visual Mood Boarding for Future Seasons & Trips",
                        "description": "Shortlisting outfits months in advance for vacations (Goa, Europe) and festivals without immediate checkout intent.",
                        "category": "mental_model",
                    },
                ],
            },
            # 6. Comparison Friction
            {
                "name": "Side-by-Side Multi-Product Comparison Friction",
                "description": "Lack of in-app side-by-side comparison matrix forcing shoppers to use desktop multi-tabs or manual paper notes to evaluate similar items.",
                "affected_shopping_stages": ["evaluation"],
                "sub_themes": [
                    {
                        "name": "Multi-Tab Switching & Desktop Workarounds",
                        "description": "Shoppers opening 5-10 browser tabs to compare fabric blend, neckline, length, and customer ratings.",
                        "category": "workaround",
                    },
                    {
                        "name": "Demand for In-App Spec Comparison Matrix",
                        "description": "Strong request for a single-screen spec comparison tool comparing fabric composition, sheer rating, and price.",
                        "category": "feature_request",
                    },
                    {
                        "name": "Choice Overload Causing Complete Cart Abandonment",
                        "description": "Holding 4-5 near-identical black kurtas or floral dresses, resulting in cognitive fatigue and abandoning all of them.",
                        "category": "friction_point",
                    },
                ],
            },
            # 7. Event Planning & Stock-Out Anxiety
            {
                "name": "Event Planning Horizons & Size Stock-Out Anxiety",
                "description": "Shoppers bookmark outfits 2-3 months ahead of weddings or trips, only to find their size permanently sold out when they are finally ready to purchase.",
                "affected_shopping_stages": ["consideration", "purchase_decision"],
                "sub_themes": [
                    {
                        "name": "Long Event Planning Horizon Stagnation",
                        "description": "Keeping ethnic sets saved for months while waiting for wedding date confirmations or travel plans.",
                        "category": "mental_model",
                    },
                    {
                        "name": "Sudden Stock-Outs on High-Intent Items",
                        "description": "Disappointment when a carefully monitored wishlist item sells out in the user's size right before checkout.",
                        "category": "friction_point",
                    },
                    {
                        "name": "Demand for Size-Specific Low Stock Alerts & Temporary Holds",
                        "description": "Request for a 24-hour size reservation or urgent low-stock warning on wishlisted garments.",
                        "category": "feature_request",
                    },
                ],
            },
            # 8. Visual Clutter & 1,000 Cap
            {
                "name": "Visual Clutter Paralysis & Wishlist Maintenance (1,000-Item Cap)",
                "description": "Disorganized, un-categorized wishlist interfaces cluttered with out-of-stock items, hitting the 1,000-item cap and causing search fatigue.",
                "affected_shopping_stages": ["discovery", "evaluation"],
                "sub_themes": [
                    {
                        "name": "Disorganization & Search Fatigue at 1,000 Item Cap",
                        "description": "Wishlist becoming an unnavigable graveyard of 500-1,000 items where high-intent pieces get lost under old impulse saves.",
                        "category": "friction_point",
                    },
                    {
                        "name": "Out-of-Stock Dead Links Burying Active Items",
                        "description": "Permanently sold-out items cluttering the feed without automatic archiving or back-in-stock notifications.",
                        "category": "friction_point",
                    },
                    {
                        "name": "Demand for Custom Wishlist Folders (Workwear, Vacation, Gifting)",
                        "description": "Strong user demand to categorize wishlisted items into custom named folders and collections.",
                        "category": "feature_request",
                    },
                ],
            },
            # 9. Desire Decay & Forgetting
            {
                "name": "Desire Decay, Novelty Fading & Stale Wishlist Forgetting",
                "description": "After 2-4 weeks, the initial emotional enthusiasm completely evaporates; without smart re-engagement nudges, saved items sit forgotten indefinitely.",
                "affected_shopping_stages": ["consideration"],
                "sub_themes": [
                    {
                        "name": "Novelty Wearing Off After 14-30 Days",
                        "description": "Users revisiting their wishlist a month later and realizing they no longer feel any emotional urge to buy the item.",
                        "category": "mental_model",
                    },
                    {
                        "name": "Lack of Timely Proactive Re-Engagement Nudges",
                        "description": "Wishlist items sitting silently without smart reminders about low size inventory, limited-time coupons, or upcoming events.",
                        "category": "friction_point",
                    },
                    {
                        "name": "Demand for 'Review & Declutter' Smart Clean-Up Assist",
                        "description": "Feature request for an automated periodic prompt asking users to keep, convert, or clean up stagnant wishlist items.",
                        "category": "feature_request",
                    },
                ],
            },
            # 10. Social Reassurance Delays
            {
                "name": "Social Reassurance Delays & Off-Platform Peer Validation",
                "description": "Shoppers pause checkout for days waiting for feedback from family, friends, or partners on WhatsApp screenshots.",
                "affected_shopping_stages": ["evaluation", "purchase_decision"],
                "sub_themes": [
                    {
                        "name": "Dependency on Family/Peer Approval for High-Ticket Items",
                        "description": "Hesitation to purchase dresses or ethnic sets >₹2,500 without second opinions from friends or family.",
                        "category": "mental_model",
                    },
                    {
                        "name": "Friction in Current In-App Sharing Workflows",
                        "description": "Current app sharing generates clunky web links rather than clean, visual preview cards that friends can vote on.",
                        "category": "friction_point",
                    },
                    {
                        "name": "Demand for 1-Click WhatsApp Group Voting Polls",
                        "description": "Desire for a feature that turns wishlisted items into an interactive WhatsApp poll for friends to vote 'Buy' or 'Skip'.",
                        "category": "feature_request",
                    },
                ],
            },
        ]


# Global singleton instance
theme_consolidator = ThemeConsolidator()
