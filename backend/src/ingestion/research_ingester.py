"""
First-Party User Research Ingester

Loads, validates, and normalizes user interview transcripts and survey exports (JSON/CSV)
into the raw data corpus schema. (Handles EC-1.20, EC-1.21, EC-1.22, EC-1.23, EC-1.24)
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd

from src.ingestion.base_scraper import sanitize_text, validate_raw_record, FORBIDDEN_PII_KEYS
from src.utils.config import RAW_DIR, INTERVIEWS_DIR, SURVEYS_DIR
from src.utils.logger import get_logger

logger = get_logger("research_ingester")


class ResearchIngester:
    """Ingests first-party qualitative research (interviews & open-ended surveys)."""

    def __init__(
        self,
        interviews_dir: Optional[Path] = None,
        surveys_dir: Optional[Path] = None,
    ):
        self.interviews_dir = Path(interviews_dir or INTERVIEWS_DIR)
        self.surveys_dir = Path(surveys_dir or SURVEYS_DIR)

    def load_interviews(self, interviews_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
        """
        Loads interview transcripts from JSON or CSV files.
        Splits transcripts into Q&A units and ensures PII sanitization.
        """
        target_dir = Path(interviews_dir or self.interviews_dir)
        records: List[Dict[str, Any]] = []

        if not target_dir.exists():
            logger.info(f"Interviews directory not found: {target_dir}")
            return records

        files = list(target_dir.glob("*.json")) + list(target_dir.glob("*.csv")) + list(target_dir.glob("*.txt"))
        if not files:
            logger.info(f"No interview files found in {target_dir}.")
            return records

        for file_path in files:
            try:
                if file_path.suffix == ".json":
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    
                    # Can be a list of interview turns or a single session object
                    items = data if isinstance(data, list) else [data]
                    for idx, item in enumerate(items):
                        p_id = item.get("participant_id") or f"P{idx+1:02d}"
                        text = item.get("transcript") or item.get("text") or item.get("response") or ""
                        q = item.get("question") or item.get("topic")

                        # Split long text at Q&A boundaries if present (EC-1.24)
                        cleaned = sanitize_text(text)
                        if not cleaned or len(cleaned.split()) < 3:
                            continue

                        rec = {
                            "record_id": str(uuid.uuid4()),
                            "source_platform": "interview",
                            "source_url": None,
                            "text": cleaned,
                            "timestamp": item.get("date") or datetime.now(timezone.utc).isoformat(),
                            "ingestion_timestamp": datetime.now(timezone.utc).isoformat(),
                            "source_type": "first_party_research",
                            "metadata": {
                                "interview_id": p_id,
                                "interview_question": q,
                                "file_name": file_path.name,
                            },
                        }
                        if validate_raw_record(rec):
                            records.append(rec)

                elif file_path.suffix == ".csv":
                    df = pd.read_csv(file_path)
                    text_cols = [c for c in df.columns if any(k in c.lower() for k in ["text", "transcript", "response", "answer"])]
                    col = text_cols[0] if text_cols else df.columns[0]

                    for idx, row in df.iterrows():
                        raw_text = str(row[col])
                        cleaned = sanitize_text(raw_text)
                        if not cleaned or len(cleaned.split()) < 3 or cleaned.lower() == "nan":
                            continue

                        p_id = str(row.get("participant_id", row.get("id", f"P{idx+1:02d}")))
                        rec = {
                            "record_id": str(uuid.uuid4()),
                            "source_platform": "interview",
                            "source_url": None,
                            "text": cleaned,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "ingestion_timestamp": datetime.now(timezone.utc).isoformat(),
                            "source_type": "first_party_research",
                            "metadata": {
                                "interview_id": p_id,
                                "file_name": file_path.name,
                            },
                        }
                        if validate_raw_record(rec):
                            records.append(rec)

                elif file_path.suffix == ".txt":
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    # Split text by double newlines or speaker turns
                    blocks = [b.strip() for b in content.split("\n\n") if len(b.strip().split()) >= 3]
                    for idx, block in enumerate(blocks):
                        cleaned = sanitize_text(block)
                        rec = {
                            "record_id": str(uuid.uuid4()),
                            "source_platform": "interview",
                            "source_url": None,
                            "text": cleaned,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "ingestion_timestamp": datetime.now(timezone.utc).isoformat(),
                            "source_type": "first_party_research",
                            "metadata": {
                                "interview_id": f"P_FILE_{file_path.stem}",
                                "turn_index": idx + 1,
                                "file_name": file_path.name,
                            },
                        }
                        if validate_raw_record(rec):
                            records.append(rec)

            except Exception as e:
                logger.warning(f"Error loading interview file {file_path}: {e}")

        logger.info(f"Loaded {len(records)} interview records.")
        return records

    def load_surveys(self, surveys_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
        """
        Loads survey response exports from CSV or JSON files.
        Each open-ended response becomes a distinct research record.
        """
        target_dir = Path(surveys_dir or self.surveys_dir)
        records: List[Dict[str, Any]] = []

        if not target_dir.exists():
            logger.info(f"Surveys directory not found: {target_dir}")
            return records

        files = list(target_dir.glob("*.csv")) + list(target_dir.glob("*.json"))
        if not files:
            logger.info(f"No survey files found in {target_dir}.")
            return records

        for file_path in files:
            try:
                if file_path.suffix == ".csv":
                    df = pd.read_csv(file_path)
                    for col in df.columns:
                        # Skip numeric/ID/timestamp columns
                        if df[col].dtype != object:
                            continue
                        
                        # Process text responses in this column
                        for idx, val in df[col].dropna().items():
                            cleaned = sanitize_text(str(val))
                            if not cleaned or len(cleaned.split()) < 3 or cleaned.lower() == "nan":
                                continue

                            rec = {
                                "record_id": str(uuid.uuid4()),
                                "source_platform": "survey",
                                "source_url": None,
                                "text": cleaned,
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                                "ingestion_timestamp": datetime.now(timezone.utc).isoformat(),
                                "source_type": "first_party_research",
                                "metadata": {
                                    "survey_question": str(col),
                                    "response_index": idx,
                                    "file_name": file_path.name,
                                },
                            }
                            if validate_raw_record(rec):
                                records.append(rec)

                elif file_path.suffix == ".json":
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    items = data if isinstance(data, list) else [data]
                    for idx, item in enumerate(items):
                        text = item.get("response") or item.get("answer") or item.get("text") or ""
                        q = item.get("question") or item.get("prompt")
                        cleaned = sanitize_text(text)
                        if not cleaned or len(cleaned.split()) < 3:
                            continue

                        rec = {
                            "record_id": str(uuid.uuid4()),
                            "source_platform": "survey",
                            "source_url": None,
                            "text": cleaned,
                            "timestamp": item.get("timestamp") or datetime.now(timezone.utc).isoformat(),
                            "ingestion_timestamp": datetime.now(timezone.utc).isoformat(),
                            "source_type": "first_party_research",
                            "metadata": {
                                "survey_question": q,
                                "file_name": file_path.name,
                            },
                        }
                        if validate_raw_record(rec):
                            records.append(rec)

            except Exception as e:
                logger.warning(f"Error loading survey file {file_path}: {e}")

        logger.info(f"Loaded {len(records)} survey records.")
        return records

    def export(self, output_dir: Optional[Path] = None) -> Dict[str, str]:
        """
        Loads all interviews and surveys and exports them as raw JSONL files.
        """
        target_dir = Path(output_dir or RAW_DIR)
        target_dir.mkdir(parents=True, exist_ok=True)

        exported_paths = {}

        # 1. Interviews
        interviews = self.load_interviews()
        if interviews:
            interview_file = target_dir / "interviews.jsonl"
            with open(interview_file, "a", encoding="utf-8") as f:
                for rec in interviews:
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            logger.info(f"Exported {len(interviews)} interview records to {interview_file}")
            exported_paths["interviews"] = str(interview_file)

        # 2. Surveys
        surveys = self.load_surveys()
        if surveys:
            survey_file = target_dir / "surveys.jsonl"
            with open(survey_file, "a", encoding="utf-8") as f:
                for rec in surveys:
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            logger.info(f"Exported {len(surveys)} survey records to {survey_file}")
            exported_paths["surveys"] = str(survey_file)

        return exported_paths
