"""
Analysis Prompts and Pydantic Schemas

Defines structured JSON schemas and prompt templates for:
1. Batch qualitative theme extraction (15-25 evidence chunks per batch).
2. Hierarchical consolidation into 2-level theme taxonomy (L1 Primary Themes + L2 Sub-Themes).
3. Research Question mapping (RQ1-RQ10).
4. Verbatim quote hallucination validator (EC-3.01).

Handles Edge Cases: EC-3.01, EC-3.02, EC-3.03, EC-3.04
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Literal, Optional
from pydantic import AliasChoices, BaseModel, Field


# =====================================================================
# 1. Pydantic Structured Output Schemas
# =====================================================================

class ThemeEvidenceItem(BaseModel):
    """Structured qualitative evidence item extracted from a source chunk."""
    theme_candidate: str = Field(
        default="",
        validation_alias=AliasChoices("theme_candidate", "insight_summary", "theme", "label", "summary"),
        description="Short descriptive theme label (e.g., 'Cross-Brand Sizing Inconsistency', 'Wishlist as Pre-Cart Holding Area')."
    )
    category: Literal[
        "friction_point",
        "mental_model",
        "feature_request",
        "workaround",
        "delight_factor",
        "decision_trigger"
    ] = Field(
        default="friction_point",
        description="Qualitative category of the evidence."
    )
    verbatim_quote: str = Field(
        ...,
        validation_alias=AliasChoices("verbatim_quote", "quote", "text_quote"),
        description="Exact verbatim excerpt from the text chunk supporting this theme."
    )
    sentiment: Literal["negative", "neutral", "positive", "mixed"] = Field(
        default="neutral",
        description="Sentiment expressed in the quote."
    )
    severity: Literal["high", "medium", "low", "relevance"] = Field(
        default="medium",
        description="Severity for frictions/issues, or relevance level for mental models and triggers."
    )
    shopping_stage: Literal[
        "discovery",
        "consideration",
        "evaluation",
        "purchase_decision",
        "post_purchase"
    ] = Field(
        default="evaluation",
        description="Stage in the user shopping journey where this behavior occurs."
    )
    user_segment_signals: List[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices("user_segment_signals", "user_signals", "signals", "persona_signals"),
        description="Signals indicating user persona (e.g., 'budget_conscious', 'occasion_shopper', 'trend_hunter')."
    )
    source_chunk_id: str = Field(
        ...,
        validation_alias=AliasChoices("source_chunk_id", "chunk_id", "source_id"),
        description="The exact chunk_id of the input text chunk."
    )


class BatchExtractionOutput(BaseModel):
    """Container for batch qualitative theme extraction output."""
    evidence_items: List[ThemeEvidenceItem] = Field(
        default_factory=list,
        description="List of structured qualitative evidence items extracted from the batch."
    )


class SubTheme(BaseModel):
    """Level 2 Sub-Theme in the hierarchical taxonomy."""
    sub_theme_id: str = Field(..., description="Unique ID for the sub-theme (e.g., 'ST-1.1').")
    name: str = Field(..., description="Clear, concise title for the sub-theme.")
    description: str = Field(..., description="Detailed description of the user behavior, friction, or mental model.")
    category: str = Field(default="friction_point", description="Primary category (friction_point, mental_model, etc.).")
    sentiment_distribution: Dict[str, int] = Field(
        default_factory=dict,
        description="Count of quotes by sentiment (e.g. {'negative': 15, 'neutral': 3})."
    )
    representative_quotes: List[Dict[str, str]] = Field(
        default_factory=list,
        description="3-5 verbatim quotes illustrating this sub-theme with quote, chunk_id, and platform."
    )
    frequency_count: int = Field(
        default=0,
        description="Number of evidence chunks supporting this sub-theme."
    )


class PrimaryTheme(BaseModel):
    """Level 1 Primary Theme in the hierarchical taxonomy."""
    theme_id: str = Field(..., description="Unique ID for the primary theme (e.g., 'T-01').")
    name: str = Field(..., description="High-level theme title (e.g., 'Wishlist as Pre-Cart & Emotional Staging Ground').")
    description: str = Field(..., description="Comprehensive synthesis of the primary theme.")
    sub_themes: List[SubTheme] = Field(
        default_factory=list,
        description="3 to 6 detailed L2 sub-themes under this primary theme."
    )
    total_evidence_count: int = Field(
        default=0,
        description="Total aggregate evidence items supporting this primary theme."
    )
    affected_shopping_stages: List[str] = Field(
        default_factory=list,
        description="Key stages affected (e.g., ['consideration', 'evaluation', 'purchase_decision'])."
    )


class HierarchicalThemeOutput(BaseModel):
    """Structured hierarchical taxonomy of consolidated themes."""
    primary_themes: List[PrimaryTheme] = Field(
        default_factory=list,
        description="6 to 10 consolidated primary themes covering the entire qualitative corpus."
    )


class RQMapping(BaseModel):
    """Mapping of consolidated thematic evidence to a core Research Question."""
    rq_id: str = Field(..., description="Research Question ID (e.g., 'RQ1').")
    rq_title: str = Field(..., description="The research question prompt.")
    answer_summary: str = Field(
        ...,
        description="Comprehensive, evidence-backed answer synthesized from qualitative research findings."
    )
    supporting_primary_theme_ids: List[str] = Field(
        default_factory=list,
        description="List of primary theme IDs (e.g. ['T-01', 'T-03']) that answer this RQ."
    )
    key_verbatim_quotes: List[str] = Field(
        default_factory=list,
        description="3 to 5 powerful verbatim user quotes directly demonstrating the finding."
    )
    confidence_score: float = Field(
        default=0.9,
        ge=0.0,
        le=1.0,
        description="Confidence score based on evidence volume and cross-platform triangulation (0.0 to 1.0)."
    )


class RQMappingOutput(BaseModel):
    """Container for all 10 Research Question mappings."""
    mappings: List[RQMapping] = Field(
        default_factory=list,
        description="List of synthesized answers mapped across all Research Questions (RQ1-RQ10)."
    )


# =====================================================================
# 2. System Prompts & Formatting Helpers
# =====================================================================

BATCH_THEME_EXTRACTION_SYSTEM_PROMPT = """You are a Principal UX Researcher & eCommerce Product Strategist analyzing consumer behavior, wishlist habits, and shopping friction points for Myntra (India's leading fashion eCommerce platform).

Your objective is to analyze a batch of qualitative customer feedback, interview transcripts, and survey responses to extract structured qualitative evidence items.

CRITICAL RULES:
1. OUTPUT JSON SCHEMA: Return a JSON array of objects with the exact keys:
   [
     {
       "source_chunk_id": "chunk_id_string",
       "theme_candidate": "Short descriptive label",
       "category": "friction_point" | "mental_model" | "feature_request" | "workaround" | "delight_factor" | "decision_trigger",
       "verbatim_quote": "Exact verbatim quote substring from the text chunk",
       "sentiment": "negative" | "neutral" | "positive" | "mixed",
       "severity": "high" | "medium" | "low" | "relevance",
       "shopping_stage": "discovery" | "consideration" | "evaluation" | "purchase_decision" | "post_purchase",
       "user_segment_signals": ["budget_conscious", "occasion_shopper", etc.]
     }
   ]

2. VERBATIM QUOTES ONLY (EC-3.01): The `verbatim_quote` MUST be an exact substring from the source text chunk. Do not alter, summarize, or paraphrase the quote.
3. CATEGORIZE ACCURATELY:
   - `friction_point`: Obstacles, anxieties, or blockers stopping purchase (e.g., sizing doubts, sheer fabric, clutter, multi-tab comparisons).
   - `mental_model`: How users conceptualize wishlists vs carts (e.g., mood board, price-drop alert tracker, buffer against impulse buying, seasonal archive).
   - `feature_request`: Explicit user desires for product capabilities (e.g., side-by-side comparison, custom folders, AI fit score, persistent restock alerts).
   - `workaround`: Hacks or third-party tools users use (e.g., WhatsApp screenshots for validation, spreadsheets, opening 4 browser tabs).
   - `decision_trigger`: What caused an item to finally convert from wishlist to cart (e.g., flash price drops, unedited customer photo reviews, urgent event).
   - `delight_factor`: Positive aspects users appreciate.
4. PRESERVE SOURCE CHUNK ID: Always attribute the evidence to the exact `source_chunk_id`.
"""


def format_batch_extraction_prompt(chunks: List[Dict[str, Any]]) -> str:
    """Formats a list of clean text chunks into a batch prompt for LLM theme extraction."""
    lines = [
        "Analyze the following qualitative text chunks and extract all relevant qualitative evidence items according to the JSON schema:\n"
    ]
    for idx, c in enumerate(chunks):
        cid = c.get("chunk_id", f"c_{idx}")
        platform = c.get("source_platform", "unknown")
        text = c.get("text", "").strip()
        lines.append(f"--- [CHUNK ID: {cid} | PLATFORM: {platform}] ---")
        lines.append(text)
        lines.append("")

    return "\n".join(lines)


HIERARCHICAL_CONSOLIDATION_SYSTEM_PROMPT = """You are a Lead UX Research Strategist synthesizing qualitative insights on Myntra wishlist and shopping behavior.

You will receive a list of candidate themes and quotes extracted across thousands of consumer reviews, user interviews, surveys, Reddit discussions, and Quora threads.

Your task is to consolidate, cluster, and synthesize these candidates into a structured 2-level hierarchy (EC-3.02):
1. **6 to 10 Primary Themes (Level 1)**: Major structural areas of the user journey (e.g., "Wishlist as Pre-Cart & Emotional Holding Ground", "Cross-Brand Sizing Uncertainty & Fit Anxiety", "Side-by-Side Comparison & Multi-Product Evaluation Friction", "Price Drop Sensitivity & Sale Timing Triggers", "Visual Clutter Paralysis & Wishlist Maintenance", "Social Validation & Unedited Real-Life Verification").
2. **3 to 6 Sub-Themes (Level 2) per Primary Theme**: Specific, actionable behavioral patterns and pain points with rich descriptions, aggregated sentiment, frequency counts, and 3-5 representative verbatim quotes per sub-theme.

CRITICAL RULES:
- Quotes in `representative_quotes` must be taken directly from the provided extracted evidence.
- Ensure exhaustive coverage without creating overlapping or redundant themes.
"""


def format_consolidation_prompt(evidence_items: List[Dict[str, Any]]) -> str:
    """Formats extracted evidence items into a consolidation prompt."""
    lines = [
        "Synthesize and consolidate the following extracted qualitative evidence items into a 2-level theme hierarchy (6-10 Primary Themes, 3-6 Sub-Themes each):\n"
    ]
    for i, item in enumerate(evidence_items):
        candidate = item.get("theme_candidate", "")
        category = item.get("category", "")
        quote = item.get("verbatim_quote", "")
        chunk_id = item.get("source_chunk_id", "")
        sentiment = item.get("sentiment", "")
        lines.append(f"[{i+1}] Theme Candidate: '{candidate}' | Category: {category} | Sentiment: {sentiment}")
        lines.append(f"    Quote: \"{quote}\" (Source: {chunk_id})")
        lines.append("")

    return "\n".join(lines)


RESEARCH_QUESTION_MAPPING_SYSTEM_PROMPT = """You are an Executive Product & UX Strategist mapping qualitative user research findings to 10 core strategic Research Questions (RQ1 to RQ10) for Myntra Wishlist product innovation.

For each Research Question, you must:
1. Synthesize a clear, executive-ready, evidence-backed answer (150-250 words).
2. Link the primary theme IDs that support the answer.
3. Select 3 to 5 compelling verbatim user quotes.
4. Provide an evidence-grounded confidence score between 0.0 and 1.0 based on data triangulation.
"""


def format_rq_mapping_prompt(
    consolidated_themes: Dict[str, Any],
    rq_list: List[Dict[str, str]],
) -> str:
    """Formats consolidated themes and research questions for RQ mapping."""
    lines = ["Here are the consolidated primary themes and sub-themes from our qualitative analysis:\n"]
    for t in consolidated_themes.get("primary_themes", []):
        lines.append(f"Theme [{t.get('theme_id')}]: {t.get('name')}")
        lines.append(f"Description: {t.get('description')}")
        for st in t.get("sub_themes", []):
            lines.append(f"  - Sub-Theme [{st.get('sub_theme_id')}]: {st.get('name')} (Count: {st.get('frequency_count')})")
        lines.append("")

    lines.append("Please synthesize detailed answers for each of the following 10 Research Questions:\n")
    for rq in rq_list:
        lines.append(f"[{rq.get('rq_id')}]: {rq.get('rq_title')}")
        lines.append(f"Context / Focus: {rq.get('focus')}")
        lines.append("")

    return "\n".join(lines)


# =====================================================================
# 3. Verbatim Quote Validator (EC-3.01)
# =====================================================================

def verify_quote_verbatim(quote: str, source_text: str) -> bool:
    """
    Validates whether an extracted quote is a genuine verbatim excerpt of the source text.
    Handles minor whitespace/case normalization.
    """
    if not quote or not source_text:
        return False

    # 1. Exact substring check
    if quote in source_text:
        return True

    # 2. Normalized alphanumeric check
    def norm(s: str) -> str:
        return re.sub(r"[^\w]", "", s.lower())

    q_norm = norm(quote)
    s_norm = norm(source_text)

    return q_norm in s_norm if len(q_norm) >= 10 else False
