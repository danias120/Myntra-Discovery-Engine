from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Any, Union

try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False

# Base Paths
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
ROOT_DIR = BACKEND_DIR.parent
DATA_DIR = BACKEND_DIR / "data"

# Load environment variables (.env in backend directory or root directory)
if DOTENV_AVAILABLE:
    if (BACKEND_DIR / ".env").exists():
        load_dotenv(BACKEND_DIR / ".env")
    elif (ROOT_DIR / ".env").exists():
        load_dotenv(ROOT_DIR / ".env")
    else:
        load_dotenv()

# API Keys & Tokens
APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")

# LLM Configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini").lower()
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

# Rate Limits (Gemini Free Tier)
GEMINI_RPM = int(os.getenv("GEMINI_RPM", "15"))
GEMINI_RPD = int(os.getenv("GEMINI_RPD", "1500"))

# Service URLs
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# Standard Data & Report Directories
RAW_DIR = DATA_DIR / "raw"
CLEAN_DIR = DATA_DIR / "clean"
THEMES_DIR = DATA_DIR / "themes"
MATRIX_DIR = DATA_DIR / "matrix"
VECTORSTORE_DIR = DATA_DIR / "vectorstore"
REPORTS_DIR = BACKEND_DIR / "reports"
RESEARCH_DIR = DATA_DIR / "research"
INTERVIEWS_DIR = RESEARCH_DIR / "interviews"
SURVEYS_DIR = RESEARCH_DIR / "surveys"
EVAL_DIR = DATA_DIR / "eval"

# Ensure runtime directories exist
for directory in [
    RAW_DIR,
    CLEAN_DIR,
    THEMES_DIR,
    MATRIX_DIR,
    VECTORSTORE_DIR,
    REPORTS_DIR,
    INTERVIEWS_DIR,
    SURVEYS_DIR,
    EVAL_DIR,
]:
    directory.mkdir(parents=True, exist_ok=True)

# Supported Ingestion Platforms
PLATFORMS = [
    "reddit",
    "quora",
    "appstore",
    "playstore",
    "youtube",
    "instagram",
    "myntra_reviews",
    "forum",
    "interview",
    "survey",
]


def validate_config() -> dict[str, bool]:
    """
    Validates the current environment setup and returns status dictionary.
    """
    status = {
        "apify_configured": bool(APIFY_API_TOKEN),
        "gemini_configured": bool(GEMINI_API_KEY),
        "youtube_configured": bool(YOUTUBE_API_KEY),
        "llm_provider": LLM_PROVIDER in ["gemini", "ollama"],
    }
    return status


def get_config_summary() -> dict[str, str | int | bool]:
    """
    Returns a safe dictionary summary of active configuration (masking secrets).
    """
    return {
        "LLM_PROVIDER": LLM_PROVIDER,
        "GEMINI_MODEL": GEMINI_MODEL,
        "OLLAMA_MODEL": OLLAMA_MODEL,
        "GEMINI_RPM": GEMINI_RPM,
        "GEMINI_RPD": GEMINI_RPD,
        "FRONTEND_URL": FRONTEND_URL,
        "BACKEND_URL": BACKEND_URL,
        "APIFY_KEY_SET": bool(APIFY_API_TOKEN),
        "GEMINI_KEY_SET": bool(GEMINI_API_KEY),
        "YOUTUBE_KEY_SET": bool(YOUTUBE_API_KEY),
    }

