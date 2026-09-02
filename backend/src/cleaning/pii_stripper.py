"""
PII Stripper Module

Strips and redacts personally identifiable information (PII) including names,
emails, phone numbers, addresses, social handles, and financial/order IDs
using deterministic regular expressions and SpaCy NER with brand whitelisting.

Handles Edge Cases: EC-2.01, EC-2.02, EC-2.03, EC-2.04, EC-2.05, EC-2.06
"""

from __future__ import annotations

import re
from typing import Any, Dict, Set
import spacy

from src.utils.logger import get_logger

logger = get_logger("pii_stripper")

# Lazy-loaded SpaCy model singleton
_nlp = None


def get_spacy_nlp():
    global _nlp
    if _nlp is None:
        try:
            _nlp = spacy.load("en_core_web_sm")
        except Exception as e:
            logger.warning(f"Could not load spacy en_core_web_sm: {e}. Falling back to blank model.")
            _nlp = spacy.blank("en")
    return _nlp


# Comprehensive Fashion Brand & Retailer Whitelist (Never redact as [NAME])
BRAND_WHITELIST: Set[str] = {
    "myntra", "ajio", "nykaa", "nykaa fashion", "meesho", "zara", "h&m", "hm",
    "mango", "nike", "puma", "adidas", "roadster", "hrx", "tokyo talkies",
    "anouk", "libas", "biba", "w", "w for woman", "fabindia", "levis", "levi's",
    "vero moda", "only", "marks & spencer", "allen solly", "van heusen",
    "louis philippe", "peter england", "woodland", "bata", "red tape", "soch",
    "indya", "rareism", "athena", "berrylush", "sassafras", "mast & harbour",
    "dressberry", "highlander", "street 9", "global desi", "and", "madame",
    "forever 21", "under armour", "asics", "skechers", "reebok", "clarks",
    "crocs", "fossil", "titan", "casio", "fastrack", "zudio", "snitch",
    "bonkers", "bewakoof", "souled store", "amazon", "flipkart", "savana",
    "fulltimestore", "tata cliq", "tatacliq", "shoppers stop", "lifestyle",
    "westside", "pantaloons", "max", "max fashion", "reliance trends"
}

# Major Indian Cities Whitelist (Preserve for demographic segmentation)
CITY_WHITELIST: Set[str] = {
    "mumbai", "delhi", "bengaluru", "bangalore", "kolkata", "chennai",
    "hyderabad", "pune", "ahmedabad", "jaipur", "surat", "lucknow",
    "kanpur", "nagpur", "indore", "thane", "bhopal", "visakhapatnam",
    "patna", "vadodara", "ghaziabad", "ludhiana", "agra", "nashik",
    "faridabad", "meerut", "rajkot", "varanasi", "srinagar", "aurangabad",
    "dhanbad", "amritsar", "navi mumbai", "allahabad", "prayagraj",
    "ranchi", "howrah", "coimbatore", "jabalpur", "gwalior", "vijayawada",
    "jodhpur", "madurai", "raipur", "kota", "guwahati", "chandigarh",
    "mysore", "mysuru", "gurgaon", "gurugram", "noida", "kochi", "dehradun",
    "mangalore", "siliguri", "udaipur", "trivandrum", "thiruvananthapuram"
}

# Regex Patterns for Deterministic PII
RE_EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
# Indian phone numbers (+91-9876543210, 09876543210, 98765 43210, 9876543210)
RE_PHONE = re.compile(r"(?:\+91[\-\s]?)?(?:0)?[6-9]\d{4}[\-\s]?\d{5}\b")
# Social media handles (@user, u/user)
RE_SOCIAL_AT = re.compile(r"(?<!\w)@[\w_.]+")
RE_SOCIAL_REDDIT = re.compile(r"\bu\/[\w_-]+")
# Credit/Debit Card numbers (16 digits with spaces or hyphens)
RE_CARD = re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b")
# Order tracking IDs (e.g. OD1234567890, TRACK87654321)
RE_ORDER_ID = re.compile(r"\b(?:OD|ORD|ORDER|TRACK|WB|IN|AWB)[A-Za-z0-9]{7,18}\b", re.IGNORECASE)
# Indian Pin codes (6 digits, starting 1-9) - with surrounding word boundary
RE_PINCODE = re.compile(r"\b[1-9][0-9]{2}\s?[0-9]{3}\b")


class PIIStripper:
    """Detects and redacts PII using multi-stage regex and SpaCy NER."""

    def __init__(self):
        self.nlp = get_spacy_nlp()

    def strip_regex_pii(self, text: str) -> str:
        """Applies fast deterministic regex redaction."""
        if not text:
            return ""

        # 1. Emails
        text = RE_EMAIL.sub("[EMAIL]", text)

        # 2. Credit Cards
        text = RE_CARD.sub("[CARD]", text)

        # 3. Order IDs
        text = RE_ORDER_ID.sub("[ORDER_ID]", text)

        # 4. Social Handles
        text = RE_SOCIAL_AT.sub("[USER]", text)
        text = RE_SOCIAL_REDDIT.sub("[USER]", text)

        # 5. Phone numbers
        text = RE_PHONE.sub("[PHONE]", text)

        return text

    def strip_ner_pii(self, text: str) -> str:
        """Applies SpaCy NER for person names and granular locations with brand protection."""
        if not text or len(text.strip()) == 0:
            return ""

        doc = self.nlp(text)
        entities_to_replace = []

        for ent in doc.ents:
            ent_lower = ent.text.strip().lower()

            # Person Names
            if ent.label_ == "PERSON":
                # Check if it is a whitelisted brand name
                if ent_lower in BRAND_WHITELIST or any(b in ent_lower for b in BRAND_WHITELIST):
                    continue
                # Don't redact common fashion terms mistakenly tagged as PERSON
                if ent_lower in {"kurta", "kurti", "lehenga", "saree", "sneakers", "denim", "eors", "dress", "myntra"}:
                    continue
                entities_to_replace.append((ent.start_char, ent.end_char, "[NAME]"))

            # Granular Locations (Redact street/building addresses, but preserve cities)
            elif ent.label_ in ("GPE", "LOC", "FAC"):
                if ent_lower in CITY_WHITELIST:
                    continue
                if ent_lower in BRAND_WHITELIST:
                    continue
                # If it's a known country or state, preserve
                if ent_lower in {"india", "karnataka", "maharashtra", "delhi", "tamil nadu", "west bengal", "kerala", "gujarat"}:
                    continue
                # Granular address / local colony
                entities_to_replace.append((ent.start_char, ent.end_char, "[LOCATION]"))

        if not entities_to_replace:
            return text

        # Sort entities in reverse order by start_char to replace without index shifts
        entities_to_replace.sort(key=lambda x: x[0], reverse=True)
        res = list(text)
        for start, end, repl in entities_to_replace:
            res[start:end] = list(repl)

        return "".join(res)

    def strip_pii(self, text: str) -> str:
        """
        Full PII redaction pipeline:
        1. Regex redaction (emails, phones, cards, handles, order IDs)
        2. SpaCy NER redaction (names, granular addresses with brand whitelisting)
        """
        if not text:
            return ""

        cleaned = self.strip_regex_pii(text)
        cleaned = self.strip_ner_pii(cleaned)
        return cleaned

    def sanitize_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitizes a full raw record object:
        - Strips PII from text
        - Removes any forbidden PII keys from root and metadata dict
        - Updates metadata with pii_removed flag
        """
        forbidden_keys = {"username", "author", "email", "user_id", "device_id", "account_id", "reviewer_name"}
        
        clean_rec = dict(record)
        # Remove root-level forbidden keys
        for k in list(clean_rec.keys()):
            if k.lower() in forbidden_keys:
                del clean_rec[k]

        # Sanitize metadata dict
        meta = clean_rec.get("metadata", {})
        if isinstance(meta, dict):
            clean_meta = dict(meta)
            for k in list(clean_meta.keys()):
                if k.lower() in forbidden_keys:
                    del clean_meta[k]
            clean_meta["pii_redacted"] = True
            clean_rec["metadata"] = clean_meta

        # Sanitize text
        clean_rec["text"] = self.strip_pii(clean_rec.get("text", ""))
        return clean_rec


# Global singleton instance
pii_stripper = PIIStripper()
