"""
Chunker Module

Implements semantic sentence-boundary chunking:
- Short reviews (<= 300 words): Retained as 1 complete chunk.
- Long reviews, forum threads, interview transcripts (> 300 words): Sentence-boundary chunking
  into 50-300 word chunks with 10-20% overlap (1-2 sentences).
- SpaCy sentence segmenter handles Indian abbreviations ("Rs.", "vs.", "e.g.", "etc.") without false splits.
- Preserves full parent metadata across all chunks.

Handles Edge Cases: EC-2.22, EC-2.23, EC-2.24, EC-2.25, EC-2.26
"""

from __future__ import annotations

import re
from typing import Any, Dict, List

from src.cleaning.pii_stripper import get_spacy_nlp
from src.utils.logger import get_logger

logger = get_logger("chunker")


class Chunker:
    """Semantic sentence-boundary chunker for qualitative retrieval and indexing."""

    def __init__(self, min_chunk_words: int = 50, max_chunk_words: int = 300, overlap_sentences: int = 1):
        self.min_chunk_words = min_chunk_words
        self.max_chunk_words = max_chunk_words
        self.overlap_sentences = overlap_sentences
        self.nlp = get_spacy_nlp()
        self.stats = {
            "total_records_chunked": 0,
            "single_chunk_records": 0,
            "multi_chunk_records": 0,
            "total_chunks_produced": 0,
        }

    def split_into_sentences(self, text: str) -> List[str]:
        """
        Splits text into sentences using SpaCy NER/sentence boundary detector (EC-2.22).
        Robust against abbreviations like 'Rs.', 'vs.', 'e.g.', 'etc.'.
        """
        if not text:
            return []

        doc = self.nlp(text)
        sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]
        if not sentences:
            # Fallback to regex split if spacy produced empty
            sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
        return sentences

    def chunk_text(self, text: str, parent_id: str = "doc") -> List[Dict[str, Any]]:
        """
        Chunks text into semantic chunks with 10-20% overlap.
        Returns a list of chunk dicts with chunk_id, chunk_index, and text.
        """
        if not text or not text.strip():
            return []

        words = text.split()
        total_words = len(words)

        # Short text: retain as single chunk (EC-2.24)
        if total_words <= self.max_chunk_words:
            return [{
                "chunk_id": f"{parent_id}_c0",
                "chunk_index": 0,
                "total_chunks": 1,
                "text": text.strip(),
                "word_count": total_words,
                "char_count": len(text.strip()),
            }]

        # Long text: Sentence-boundary chunking with overlap (EC-2.25)
        sentences = self.split_into_sentences(text)
        chunks: List[str] = []
        current_sentences: List[str] = []
        current_word_count = 0

        for sent in sentences:
            sent_words = len(sent.split())
            if current_word_count + sent_words > self.max_chunk_words and current_sentences:
                chunk_str = " ".join(current_sentences).strip()
                chunks.append(chunk_str)
                # Keep overlap sentences
                overlap = current_sentences[-self.overlap_sentences:] if self.overlap_sentences > 0 else []
                current_sentences = list(overlap)
                current_word_count = sum(len(s.split()) for s in current_sentences)

            current_sentences.append(sent)
            current_word_count += sent_words

        if current_sentences:
            chunk_str = " ".join(current_sentences).strip()
            if chunks and current_word_count < self.min_chunk_words:
                # Merge small trailing sentence into previous chunk if within reason
                chunks[-1] = f"{chunks[-1]} {chunk_str}".strip()
            else:
                chunks.append(chunk_str)

        total_chunks = len(chunks)
        results = []
        for idx, c_text in enumerate(chunks):
            c_words = len(c_text.split())
            results.append({
                "chunk_id": f"{parent_id}_c{idx}",
                "chunk_index": idx,
                "total_chunks": total_chunks,
                "text": c_text,
                "word_count": c_words,
                "char_count": len(c_text),
            })

        return results

    def chunk_record(self, record: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Chunks a full record dict, propagating all parent metadata to each chunk (EC-2.26).
        """
        self.stats["total_records_chunked"] += 1
        parent_id = record.get("record_id", "rec")
        raw_text = record.get("text", "")

        chunks = self.chunk_text(raw_text, parent_id=parent_id)

        if len(chunks) == 1:
            self.stats["single_chunk_records"] += 1
        else:
            self.stats["multi_chunk_records"] += 1

        self.stats["total_chunks_produced"] += len(chunks)

        chunked_records = []
        for c in chunks:
            rec_chunk = dict(record)
            rec_chunk["parent_id"] = parent_id
            rec_chunk["chunk_id"] = c["chunk_id"]
            rec_chunk["chunk_index"] = c["chunk_index"]
            rec_chunk["total_chunks"] = c["total_chunks"]
            rec_chunk["text"] = c["text"]
            rec_chunk["word_count"] = c["word_count"]
            rec_chunk["char_count"] = c["char_count"]
            chunked_records.append(rec_chunk)

        return chunked_records

    def get_stats(self) -> Dict[str, Any]:
        """Returns chunker statistics."""
        return self.stats


# Global singleton instance
chunker = Chunker()
