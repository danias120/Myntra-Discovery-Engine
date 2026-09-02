# Edge Cases & Corner Scenarios

> **Source:** Derived from [architecture.md](file:///Users/daniamacbook/Desktop/NL%20Myntra/Docs/architecture.md) and [implementation-plan.md](file:///Users/daniamacbook/Desktop/NL%20Myntra/Docs/implementation-plan.md)
> **Purpose:** Catalog every corner scenario that could break, degrade, or silently corrupt the Discovery Engine pipeline — with detection strategies and handling instructions.

---

## How to Use This Document

Each edge case follows a consistent format:

| Field | Description |
|---|---|
| **ID** | Unique identifier (e.g., `EC-1.01`) — prefix = pipeline stage |
| **Scenario** | What happens |
| **Trigger** | How/when this occurs |
| **Impact** | What breaks or degrades if unhandled |
| **Detection** | How to spot it |
| **Handling** | What the code should do |
| **Severity** | 🔴 Critical · 🟡 Medium · 🟢 Low |

---

## Stage 1: Data Sourcing & Ingestion

### 1.1 — Apify Free-Tier & API Quota Issues

| ID | Scenario | Trigger | Impact | Detection | Handling | Severity |
|---|---|---|---|---|---|---|
| EC-1.01 | **Apify free-tier quota exhausted mid-scrape** | 30 actor-seconds consumed before all platforms scraped | Remaining platforms get zero data | `ApifyClient` raises `QuotaExhaustedError`; check `quota_remaining` after each call | Stop Apify calls immediately. Log which platforms were skipped. Fall back to Python libraries (`google-play-scraper`, `app-store-scraper`) for app reviews. Prioritize high-value sources (Reddit, App Store) first in run order. | 🔴 |
| EC-1.02 | **YouTube Data API v3 daily quota exhausted** | 10,000 units/day hit (each `commentThreads.list` = 1 unit, `search.list` = 100 units) | No more YouTube comments via API for the day | HTTP 403 with `quotaExceeded` reason | Switch to Apify `streamers--youtube-scraper` as fallback. Log quota usage. Resume API the next day. | 🟡 |
| EC-1.03 | **YouTube API key invalid or revoked** | Key deleted from Google Cloud Console, or billing disabled | All YouTube API calls fail with 400/403 | HTTP 400 or 403 on first call | Log error clearly. Fall back to Apify actor entirely. Alert user to regenerate key. | 🟡 |
| EC-1.04 | **Apify actor deprecated or renamed** | Apify community actor author removes/renames their actor | `ActorNotFoundError` or silent 404 | Actor run creation fails | Maintain a `FALLBACK_ACTORS` map per platform. Try the next actor in the list. If all fail, log and skip that platform. | 🟡 |
| EC-1.05 | **Apify actor returns empty dataset** | Query terms don't match any content on the platform, or actor is broken | Zero records for that platform | `len(dataset_items) == 0` after actor completes | Log warning. Try with broader/alternative query terms from `extended` list. If still empty, document the gap — don't fabricate data. | 🟡 |
| EC-1.06 | **Apify actor times out** | Actor takes longer than timeout (free tier has limited compute) | Partial or no data | Actor run status = `TIMED_OUT` | Retry once with reduced `max_results`. If still times out, use whatever partial results were returned and log. | 🟡 |

### 1.2 — Platform-Specific Scraping Failures

| ID | Scenario | Trigger | Impact | Detection | Handling | Severity |
|---|---|---|---|---|---|---|
| EC-1.07 | **Myntra product page structure changes** | Myntra redesigns their review section HTML | `bs4` selectors return `None`; scraper produces empty/malformed records | Parse failure count > 50% of attempted URLs | Halt Myntra scraper. Log failed URLs with the HTML snippet. Fall back to Apify web scraper actor. Notify for selector update. | 🟡 |
| EC-1.08 | **Myntra blocks scraping IP / returns CAPTCHA** | Rate limit exceeded, or anti-bot detection triggered | HTTP 403 / CAPTCHA HTML instead of product page | Response doesn't contain expected review selectors; status code != 200 | Reduce request rate. Add random delays (2–5s). If blocked repeatedly, switch entirely to Apify actor (which uses rotating proxies). | 🔴 |
| EC-1.09 | **Instagram scraper returns only image posts (no text)** | Hashtag search returns photo-only posts with no captions or comments | Records have empty `text` fields | `len(record["text"].strip()) == 0` | Filter out text-empty records. Try alternative hashtags. Instagram may have limited text content — document as a coverage gap if persistent. | 🟢 |
| EC-1.10 | **Reddit subreddit is private or banned** | Subreddit set to private or banned by admins (e.g., r/Myntra goes private) | Zero results from that subreddit | Apify returns empty or error for that subreddit | Skip the subreddit. Log it. Redistribute query terms to other subreddits (`r/india`, `r/IndianFashionAddicts`). | 🟢 |
| EC-1.11 | **Reddit posts have deleted/removed comments** | Moderator removals, user deletions | Comments show as `[deleted]` or `[removed]` | `text == "[deleted]"` or `text == "[removed]"` | Filter out deleted/removed comments during ingestion (not downstream). Don't count them as records. | 🟢 |
| EC-1.12 | **Quora answers are behind login wall** | Quora shows partial content for non-logged-in users | Truncated text ("Read more..." without the full answer) | Text ends with "..." or "Read more" and is < 100 chars | If using Apify, the actor should handle login walls. If not, discard truncated answers < 50 words. | 🟡 |
| EC-1.13 | **Forum site is down or returns 5xx** | Target fashion forum server is unreachable | Zero forum data | HTTP 5xx or `ConnectionError` | Retry 3 times with exponential backoff (5s, 15s, 45s). If still down, skip that forum. Document the gap. | 🟢 |
| EC-1.14 | **Forum `robots.txt` disallows scraping** | Forum explicitly blocks crawlers | Ethical violation if scraped | `robots.txt` parser returns `disallowed` for target paths | Do NOT scrape. Log as "skipped: robots.txt disallows". Document the coverage gap. | 🔴 |

### 1.3 — Data Quality Issues at Ingestion

| ID | Scenario | Trigger | Impact | Detection | Handling | Severity |
|---|---|---|---|---|---|---|
| EC-1.15 | **Duplicate raw records within a single scrape run** | Apify actor or API returns paginated results with overlapping pages | Inflated record counts | Duplicate `source_url` or identical `text` hashes within a single platform's output | Deduplicate by `source_url` within each scraper before export. Add a `seen_urls` set per run. | 🟡 |
| EC-1.16 | **Record text is HTML/markdown instead of plain text** | Scraper doesn't strip HTML tags from source | HTML tags pollute the corpus | Regex check for `<[a-z]+>` or `&amp;`, `&lt;` etc. | Strip HTML with `BeautifulSoup.get_text()` before creating `RawRecord`. | 🟡 |
| EC-1.17 | **Record text is in a non-Indian language (French, Arabic, etc.)** | Broad query terms surface global results | Non-relevant records in the corpus | Language detection (e.g., `langdetect`) returns non-`en`/`hi` | Filter out at ingestion level. Keep only `en`, `hi`, and Hinglish. Log filtered counts by language. | 🟢 |
| EC-1.18 | **Timestamp is missing or malformed** | Some APIs don't return timestamps, or format varies | Cannot enforce recency window | `timestamp` field is `null` or fails `dateutil.parser.parse()` | Set `timestamp` to `null` and allow through — recency filter uses `ingestion_timestamp` as fallback. Log count of missing timestamps. | 🟢 |
| EC-1.19 | **Record text contains only emojis / no actual words** | Social media responses that are only 😍👍🔥 | No analyzable text | `word_count == 0` after stripping non-alphanumeric characters | Filter out during spam filtering (Phase 2). Flag as boilerplate. | 🟢 |

### 1.4 — User Research Data Issues

| ID | Scenario | Trigger | Impact | Detection | Handling | Severity |
|---|---|---|---|---|---|---|
| EC-1.20 | **Interview transcript file is malformed JSON/CSV** | Manual data preparation error | Ingester crashes or skips the file | `json.JSONDecodeError` or `csv.Error` on load | Catch the exception. Log the file path and error. Skip that file. Continue with other files. Alert user to fix the file. | 🟡 |
| EC-1.21 | **Interview data contains un-anonymized participant names** | Researcher forgot to anonymize before placing in `data/research/` | PII leaks into the pipeline | Presence of `PERSON` NER entities in text, or non-anonymized ID patterns (real names instead of P01, P02) | Run PII stripper on research data too (even though it's supposed to be pre-anonymized). Log a WARNING if PII is detected. Don't silently pass through. | 🔴 |
| EC-1.22 | **Survey response file has no open-ended text fields** | All responses are multiple-choice with no qualitative data | Zero useful records from surveys | All text fields are empty or contain only numbers/ratings | Log warning. Skip the file. Document that survey data didn't contribute qualitative content. | 🟢 |
| EC-1.23 | **Research data directory is empty** | User hasn't placed any research files yet | `ResearchIngester` finds nothing | `os.listdir()` returns empty for `interviews/` and `surveys/` | This is valid — research data is optional. Log info-level message: "No research data found. Proceeding with scraped sources only." Don't error. | 🟢 |
| EC-1.24 | **Interview transcript is extremely long (>50K tokens)** | Full unedited interview recording transcript | Single record blows up chunker and LLM context | `len(text.split()) > 10000` | Split at Q&A boundaries during ingestion (not just downstream chunking). Each Q&A exchange becomes a separate record. | 🟡 |

---

## Stage 2: Cleaning & Normalization

### 2.1 — PII Stripping Edge Cases

| ID | Scenario | Trigger | Impact | Detection | Handling | Severity |
|---|---|---|---|---|---|---|
| EC-2.01 | **Hinglish text contains PII that regex misses** | Indian names written in English but not in spaCy's NER training data (e.g., "Priyanka told me...") | PII survives into clean corpus | Manual review of Hinglish chunks; spaCy NER `PERSON` recall on Hinglish < 70% | Add a curated list of common Indian first names as a supplementary regex pattern. Flag Hinglish chunks for manual review. Conservative approach: strip anything that looks like a name. | 🔴 |
| EC-2.02 | **Brand names mistakenly stripped as PII** | spaCy NER classifies "Myntra", "AJIO", "Zara" as `PERSON` or `ORG` and removes them | Critical product/brand context lost | Check if stripped entities are in the `KEEP_ENTITIES` allowlist | Maintain an allowlist of fashion brand names and platform names that should NEVER be stripped. Check against allowlist before redacting. | 🟡 |
| EC-2.03 | **PII pattern matches legitimate content** | `@handle` regex matches email-style product codes (e.g., `SKU@myntra2024`); phone regex matches product IDs with 10 digits | Legitimate text corrupted | Over-stripping count is unusually high relative to record count | Tighten regex patterns: `@handle` only if preceded by whitespace or start-of-line; phone only if preceded by `+` or starts with `[6-9]` (Indian numbers). Log all stripped content (hashed) for audit. | 🟡 |
| EC-2.04 | **spaCy model fails to load** | `en_core_web_sm` not downloaded, or corrupted install | PII stripper crashes | `OSError` when loading spaCy model | Catch the error. Fall back to regex-only PII stripping (no NER). Log a WARNING that name detection is degraded. Add spaCy download to `make install`. | 🟡 |

### 2.2 — Deduplication Edge Cases

| ID | Scenario | Trigger | Impact | Detection | Handling | Severity |
|---|---|---|---|---|---|---|
| EC-2.05 | **Cross-platform exact duplicates** | Same user posts the same review on App Store and Play Store, or copypastes between platforms | Duplicate evidence inflates theme frequency | MinHash LSH detects similarity ≥ 0.85 | Keep the record from the platform with richer metadata (e.g., rating). Remove the other. Log the duplicate pair. | 🟡 |
| EC-2.06 | **Near-duplicates with significant differences** | Two reviews discuss the same issue but from different angles (85% similar text but different conclusions) | Legitimate separate viewpoints merged | MinHash similarity ≥ 0.85 but manual review shows distinct content | Accept the 0.85 threshold but log borderline cases (0.80–0.90). Consider raising threshold to 0.90 if too many legitimate records are removed. | 🟡 |
| EC-2.07 | **Very short texts all appear as duplicates** | Records like "size issue" and "size problem" are only 2–3 words — high similarity by chance | Legitimate short records removed | High dedup rate (>30%) AND average word count of removed records < 15 | Exempt records with < 15 words from MinHash dedup. Use exact-match dedup only for short texts. | 🟡 |
| EC-2.08 | **Memory exhaustion building LSH index** | Corpus exceeds 50K records; MinHash LSH index consumes too much RAM | `MemoryError` or system OOM kill | System memory usage exceeds 80% during dedup | Process in batches of 10K records. Build LSH index incrementally. Use disk-backed LSH if available. | 🟢 |

### 2.3 — Filtering & Chunking Edge Cases

| ID | Scenario | Trigger | Impact | Detection | Handling | Severity |
|---|---|---|---|---|---|---|
| EC-2.09 | **Relevance filter removes too many records (>70%)** | Query terms at ingestion were too broad, pulling in many irrelevant results | Corpus is smaller than expected | `filtered_count / total_count > 0.70` | Log a WARNING. Review the Tier 1 keyword list — it may be too strict. Lower the LLM classifier threshold. Don't silently continue with a tiny corpus. | 🟡 |
| EC-2.10 | **Relevance filter LLM call fails** | Gemini rate limit hit, or Ollama not running | Tier 2 (ambiguous records) can't be classified | LLM call throws exception | Default to KEEP for ambiguous records (conservative: don't discard without evidence). Log that LLM filter was skipped. | 🟡 |
| EC-2.11 | **Chunker produces a chunk with 0 words** | Splitting at sentence boundary produces an empty segment (e.g., between two newlines) | Empty chunks pollute the corpus | `len(chunk["text"].strip()) == 0` | Filter out zero-length chunks after chunking. Don't assign `chunk_id` to empty chunks. | 🟢 |
| EC-2.12 | **Chunker splits mid-sentence** | Sliding window cuts at exactly 300 tokens, mid-word or mid-sentence | Broken sentences in corpus | Chunk ends without sentence-ending punctuation | Use sentence-boundary-aware splitting: find the last `.`, `!`, `?` before the 300-token limit. Allow up to 350 tokens if it avoids a mid-sentence split. | 🟡 |
| EC-2.13 | **Single record produces 50+ chunks** | Very long forum thread or interview transcript | One record dominates the corpus | `chunk_count_for_record > 30` | Cap at 30 chunks per parent record. Take the first 30. Log that the record was truncated. | 🟢 |
| EC-2.14 | **All records from one platform are filtered as spam** | An entire platform's data is low-quality (e.g., all Play Store reviews are < 10 words) | Zero contribution from that platform | Post-filter count for platform = 0 | Log a WARNING per platform. Document the gap. Don't error — the pipeline should continue with remaining platforms. | 🟡 |
| EC-2.15 | **Clean corpus has fewer than 500 chunks** | Aggressive filtering + thin data sources | Insufficient data for meaningful thematic analysis | `wc -l data/clean/corpus.jsonl < 500` | Log a CRITICAL warning. Allow pipeline to continue but flag in the final report that results are based on thin data. Consider re-running ingestion with broader query terms. | 🔴 |
| EC-2.16 | **Non-English text that isn't Hindi/Hinglish** | Tamil, Telugu, Bengali fashion reviews mixed in | Non-analyzable text in corpus | `langdetect` returns `ta`, `te`, `bn`, etc. | Filter out during spam filter. Keep only `en`, `hi`. Log filtered counts by detected language. | 🟢 |

---

## Stage 3: Thematic Analysis Engine

### 3.1 — LLM Response Issues

| ID | Scenario | Trigger | Impact | Detection | Handling | Severity |
|---|---|---|---|---|---|---|
| EC-3.01 | **LLM returns invalid JSON** | Model outputs markdown-wrapped JSON (` ```json ... ``` `), or includes preamble text before the JSON | JSON parse fails; batch is lost | `json.JSONDecodeError` | Step 1: Strip markdown code fences and preamble. Step 2: Retry with "Fix this JSON and return valid JSON only" prompt. Step 3: If retry fails, log the batch and skip. Track failure rate — should be < 5%. | 🟡 |
| EC-3.02 | **LLM returns valid JSON but wrong schema** | Model returns themes without `chunk_ids`, or uses different field names | Theme-chunk linkage is broken | Schema validation fails (missing required fields) | Attempt to map known alternative field names (e.g., `source_ids` → `chunk_ids`). If critical fields are genuinely missing, retry the batch with a more explicit schema in the prompt. | 🟡 |
| EC-3.03 | **LLM hallucinates chunk_ids** | Model invents chunk_ids that don't exist in the input batch | Theme evidence points to non-existent chunks | Cross-reference returned `chunk_ids` against the batch's actual `chunk_ids` | Validate every returned `chunk_id` against the input. Strip any hallucinated IDs. If a theme has zero valid chunk_ids after validation, discard the theme. | 🔴 |
| EC-3.04 | **LLM produces too few themes (< 3 from a 20-chunk batch)** | Batch is homogeneous (all about the same topic), or model under-segments | Under-representation of diversity in micro-themes | `len(micro_themes) < 3` for a batch | Log the batch. Accept the themes — homogeneous batches legitimately produce fewer themes. Only flag if > 30% of batches produce < 3 themes. | 🟢 |
| EC-3.05 | **LLM produces too many themes (> 20 from a 20-chunk batch)** | Model over-segments, treating each chunk as its own theme | Explosion of micro-themes; consolidation phase overloaded | `len(micro_themes) > batch_size` | Accept but log. The consolidation pass (Pass 2) will merge them. If this happens consistently, tune the prompt: "Extract 3–10 distinct themes, not one per snippet." | 🟡 |
| EC-3.06 | **LLM response is empty or just whitespace** | API glitch, model confusion, or safety filter triggered | Lost batch | `len(response.strip()) == 0` | Retry once. If still empty, log and skip the batch. Check if the input contained content that triggered safety filters (profanity, sensitive topics). | 🟡 |
| EC-3.07 | **Gemini safety filter blocks the request** | Input chunks contain profanity, explicit content, or sensitive topics | API returns `SAFETY` block reason | Gemini API response has `finish_reason: SAFETY` or `block_reason` | Remove the flagged chunks from the batch. Re-run with remaining chunks. If the entire batch is blocked, log and skip. Consider sanitizing profanity before sending. | 🟡 |
| EC-3.08 | **LLM context window exceeded** | Consolidation pass has > 200 micro-themes, exceeding Gemini's context limit | API error or truncated response | HTTP 400 with token limit error, or response is cut off mid-JSON | Split micro-themes into groups of 50. Consolidate each group. Then consolidate the results. Recursive map-reduce. | 🟡 |

### 3.2 — Theme Quality Issues

| ID | Scenario | Trigger | Impact | Detection | Handling | Severity |
|---|---|---|---|---|---|---|
| EC-3.09 | **Themes are too vague** | LLM produces themes like "General Dissatisfaction" or "Shopping Issues" | Report is not actionable for stakeholders | Theme name length > 5 words AND description is generic (no specific friction mentioned) | Add prompt instruction: "Each theme must name a SPECIFIC friction or behavior, not a category." Re-run consolidation if > 30% of themes are vague. Human review checkpoint. | 🟡 |
| EC-3.10 | **Two final themes are near-duplicates** | Consolidation pass didn't merge similar themes | Inflated theme count; confusing report | Cosine similarity between theme descriptions > 0.85 (using BGE-small embeddings) | Post-consolidation similarity check. If duplicates found, merge them manually or re-run consolidation with explicit instruction to merge. | 🟡 |
| EC-3.11 | **A research question has zero themes mapped to it** | No corpus evidence exists for that RQ (e.g., RQ9 about segment differences) | Incomplete RQ coverage in the report | `rq_coverage.json` has `uncovered` list with entries | Run `ResearchMapper.fill_gaps()`: targeted LLM pass over corpus specifically looking for evidence for the uncovered RQ. If genuinely no evidence, document the gap explicitly in the report. | 🔴 |
| EC-3.12 | **Theme has evidence from only one platform** | All supporting chunks come from Reddit, no cross-platform corroboration | Low confidence in the theme; potential platform bias | `len(theme["source_platforms"]) == 1` | Don't discard — single-platform themes are valid. But flag as `single_source` in metadata. Note in the report: "This theme is based on evidence from [platform] only." | 🟢 |
| EC-3.13 | **Theme evidence contains surviving PII** | PII stripper missed something in the evidence snippets | PII in the final report | Final regex pass on theme evidence snippets detects `@handles`, emails, names | Run a final PII regex pass on all theme evidence before writing `themes.jsonl`. Strip any remaining PII. Log as CRITICAL — the Phase 2 stripper has a bug. | 🔴 |
| EC-3.14 | **Micro-theme extraction batch order affects results** | Different shuffles of chunks into batches produce different themes | Non-deterministic theme output | Re-running with different seeds produces significantly different micro-themes | Set a fixed random seed for batch formation. Document that results may vary slightly across runs. Accept this as inherent LLM non-determinism. | 🟢 |

---

## Stage 4: Opportunity Quantification & Prioritization

### 4.1 — Scoring Edge Cases

| ID | Scenario | Trigger | Impact | Detection | Handling | Severity |
|---|---|---|---|---|---|---|
| EC-4.01 | **Theme has chunk_count = 0** | Bug in theme-chunk linkage from Phase 3 | Division by zero in frequency score; theme shouldn't exist | `chunk_count == 0` | Discard the theme. Log as ERROR — this indicates a Phase 3 bug. Themes without evidence are invalid. | 🔴 |
| EC-4.02 | **All themes score within a narrow range (e.g., 40–50)** | Homogeneous corpus; no clear differentiation between themes | Ranking is arbitrary; no clear prioritization for stakeholders | `max_score - min_score < 15` | Log warning. Report honestly: "Themes are similarly weighted; no dominant opportunity emerged." Don't artificially spread scores. | 🟡 |
| EC-4.03 | **LLM gives all themes the same purchase-delay score** | Model doesn't differentiate between themes | One scoring dimension is flat; distorts composite score | `std_dev(purchase_delay_scores) < 5` | Retry with a more detailed prompt that forces differentiation: "You MUST rank them. No two themes should receive the same score." If still flat, weight the score lower. | 🟡 |
| EC-4.04 | **LLM returns purchase-delay score outside 0–100 range** | Model outputs 150 or -10 | Score calculation is wrong | `score < 0 or score > 100` | Clamp to [0, 100]. Log the out-of-range value. If > 30% of scores are out of range, the prompt needs fixing. | 🟢 |
| EC-4.05 | **Two themes have identical composite scores** | Mathematical tie | Ambiguous ranking | `score_A == score_B` | Use `platform_spread_score` as tiebreaker (more cross-platform evidence = higher rank). If still tied, use `chunk_count`. | 🟢 |

### 4.2 — Segment Slicing Edge Cases

| ID | Scenario | Trigger | Impact | Detection | Handling | Severity |
|---|---|---|---|---|---|---|
| EC-4.06 | **Segment has < 10 supporting chunks** | Thin data for a segment category (e.g., "men_formal" has only 4 mentions) | Spurious segment conclusions from insufficient data | `segment_chunk_count < 10` | Exclude from the main report. Flag as `low_confidence` in `matrix.json`. Document in segment_view.md: "Insufficient data for this segment." | 🟡 |
| EC-4.07 | **Segment has 5–9 chunks (borderline)** | Edge case around the minimum threshold | May or may not be reportable | `5 <= segment_chunk_count < 10` | Include in `matrix.json` with `low_confidence: true` flag. Exclude from the main report prose. Mention in an appendix. | 🟢 |
| EC-4.08 | **No price mentions found in any chunk** | Users don't mention specific prices or price ranges | Entire "price band" segment dimension is empty | All `price_band` categories have 0 chunks | Skip the price band dimension entirely for that theme. Document: "Price band segmentation not possible — no price signals in corpus." | 🟢 |
| EC-4.09 | **Keyword-based segment classification is ambiguous** | A chunk mentions both "wedding" and "office" — which occasion segment? | Chunk is double-counted or miscategorized | Chunk matches keywords from multiple segment categories | Allow multi-labeling. A chunk can belong to multiple segments. Document that segment counts may sum to more than total chunks. | 🟢 |
| EC-4.10 | **Segment keyword list misses Indian-specific terms** | Keywords are English-centric; miss terms like "lehenga", "kurta set", "sherwaani" | Under-counting of ethnic fashion segments | Low counts in ethnic categories despite corpus containing Hindi fashion terms | Add comprehensive Indian fashion vocabulary to `CATEGORY_KEYWORDS`. Include Hinglish terms. Iterate keyword list based on corpus content. | 🟡 |

---

## Stage 5: RAG Assistant

### 5.1 — Embedding & Indexing Edge Cases

| ID | Scenario | Trigger | Impact | Detection | Handling | Severity |
|---|---|---|---|---|---|---|
| EC-5.01 | **BGE-small model fails to download** | HuggingFace is down, or network firewall blocks model download | Embedder cannot initialize | `OSError` or `ConnectionError` from `sentence-transformers` | Cache the model locally after first download (`~/.cache/huggingface/`). If download fails, check for cached version. If no cache, abort with clear error message. | 🔴 |
| EC-5.02 | **ChromaDB index is corrupted** | Incomplete write during power failure, or disk full during index build | Queries fail or return garbage | `chromadb` raises `InvalidCollectionException` or returns 0 results for all queries | Delete the `data/vectorstore/` directory. Re-run `--rag-build` to rebuild from scratch. Index build is idempotent. | 🟡 |
| EC-5.03 | **Chunk text is empty string during embedding** | Bug in upstream cleaning; empty text slips through | `sentence-transformers` may produce zero vectors or error | `len(chunk["text"].strip()) == 0` | Filter out empty-text chunks before embedding. Log as WARNING. | 🟢 |
| EC-5.04 | **Embedding dimension mismatch** | Config says 384-dim but a different BGE model is loaded (e.g., bge-base at 768-dim) | ChromaDB collection rejects mismatched vectors | `chromadb.errors.DimensionMismatchError` | Validate embedding dimension matches `RAGConfig.EMBEDDING_DIM` before indexing. If mismatch, clear and rebuild the collection. | 🔴 |
| EC-5.05 | **Vector store runs out of disk space** | Railway free-tier has limited storage; large corpus fills disk | Index build fails partway | `OSError: No space left on device` | Estimate index size before build (384-dim × 4 bytes × chunk_count + metadata overhead). If estimated size > 80% of available disk, warn user. Consider using FAISS with IVF compression. | 🟡 |
| EC-5.06 | **Re-indexing doesn't remove old chunks** | Corpus changed between runs but old chunks remain in vector store | Stale/deleted chunks returned in queries | `vectorstore.count() > len(current_corpus)` | Use `upsert` with collection clearing: drop and recreate collections before re-indexing. Or track chunk_ids and remove orphans. | 🟡 |

### 5.2 — Retrieval & Reranking Edge Cases

| ID | Scenario | Trigger | Impact | Detection | Handling | Severity |
|---|---|---|---|---|---|---|
| EC-5.07 | **Query returns zero results from vector store** | Query is completely off-topic (e.g., "What is the weather today?") | No context for the LLM to generate from | `len(candidates) == 0` | Return a canned response: "I don't have information about this topic. I can answer questions about fashion wishlisting and purchase behavior on Myntra." | 🟡 |
| EC-5.08 | **All retrieved chunks have very low similarity scores** | Query is tangentially related but no strong matches | LLM generates a low-confidence answer from weak evidence | All similarity scores < 0.3 (or configurable threshold) | Add a minimum similarity threshold in `rag_config.py`. If all results are below threshold, return: "I found some loosely related information, but I'm not confident enough to provide a definitive answer." | 🟡 |
| EC-5.09 | **Cross-encoder reranker flips the order incorrectly** | Reranker model is weak on domain-specific queries | Best BGE results get pushed down; worse results go to LLM | Retrieval benchmark shows reranker DECREASES Recall@5 vs. BGE-only | Make reranker toggleable (`RERANKER_ENABLED = False` in `rag_config.py`). If benchmark shows negative lift, disable reranker and use BGE-only ranking. | 🟡 |
| EC-5.10 | **Cross-encoder model fails to load** | Model not cached, HuggingFace down | Reranker step crashes | `OSError` from `CrossEncoder` initialization | Fall back to BGE-only ranking (skip reranking). Log WARNING. Cache models locally. | 🟡 |
| EC-5.11 | **Query is in Hindi but corpus is mostly English** | User asks "myntra pe wishlist mein kyun rakhte ho?" | BGE-small (English-trained) produces poor Hindi embeddings; retrieval misses relevant chunks | Low Recall@5 on Hindi benchmark queries | Translate Hindi queries to English before embedding (using Gemini: "Translate this to English: ..."). Then embed the English version. Also embed the original Hindi to catch Hinglish content. Merge results from both embeddings. | 🟡 |
| EC-5.12 | **Query matches theme summaries but not corpus chunks** | Query aligns with a macro-theme but no individual chunk is a strong match | Answer is based on theme descriptions only (synthesized, not raw evidence) | Retrieved results are 100% from `theme_summaries` collection, 0% from `corpus_chunks` | Still valid — theme summaries contain evidence. But note in the response: "This answer is based on synthesized theme analysis." | 🟢 |
| EC-5.13 | **Duplicate chunks in retrieved results** | Same chunk appears in both `corpus_chunks` and as evidence in `theme_summaries` | Redundant context wastes LLM token budget | Duplicate `chunk_id` across retrieved results | Deduplicate by `chunk_id` in the retriever. Keep the result with the higher relevance score. | 🟢 |

### 5.3 — Generation & Citation Edge Cases

| ID | Scenario | Trigger | Impact | Detection | Handling | Severity |
|---|---|---|---|---|---|---|
| EC-5.14 | **LLM generates answer with zero citations** | Model ignores the citation instruction in the system prompt | Untraceable claims; violates evidence traceability principle | `_validate_citations()` returns `citation_count == 0` | Retry ONCE with an appended instruction: "You MUST cite every claim with [Source: ...]. This is mandatory." If still zero citations, return the response with a disclaimer: "⚠️ This response could not be verified against sources." | 🔴 |
| EC-5.15 | **LLM cites chunk_ids that weren't in the retrieved context** | Model hallucinated a chunk_id | False traceability — user clicks a citation that leads nowhere | `_validate_citations()` returns `hallucinated_citations > 0` | Strip hallucinated citations from the response. Log as WARNING. If > 50% of citations are hallucinated, regenerate the response. | 🔴 |
| EC-5.16 | **LLM response contradicts the retrieved evidence** | Model hallucination or misinterpretation | Misleading answer | Difficult to detect automatically; requires semantic comparison | Include retrieved snippets alongside the answer in the response. Users can compare. Add a "View Sources" toggle in the frontend for transparency. | 🟡 |
| EC-5.17 | **LLM generates PII in its response** | Model reconstructs a name from context cues (e.g., "As user Priya mentioned...") | PII leak in RAG response | Regex PII scan on the generated response | Run the same PII regex patterns on every generated response. Strip any detected PII before returning. Log as CRITICAL. | 🔴 |
| EC-5.18 | **LLM response exceeds token budget** | Model produces a very long answer (>2000 tokens) | Slow response time; streaming delay | Response token count > `MAX_RESPONSE_TOKENS` config | Set `max_output_tokens` in the LLM call parameters. If exceeded, truncate and append "... [Response truncated for length]." | 🟢 |
| EC-5.19 | **Streaming response breaks mid-stream** | Network error between Railway and Vercel, or LLM API disconnects | User sees partial answer | SSE connection drops; frontend receives `EventSource` error | Frontend: display whatever was received + "⚠️ Response was interrupted. Try again." Backend: log the error. | 🟡 |
| EC-5.20 | **User sends empty or whitespace-only query** | Frontend doesn't validate input | Embedder produces meaningless vector; garbage results | `len(query.strip()) == 0` | Validate in both frontend (disable send button) and backend (return 400). | 🟢 |
| EC-5.21 | **User sends extremely long query (>1000 words)** | User pastes an entire document as a query | Token budget blown on the query itself; embedding quality degrades | `len(query.split()) > 200` | Truncate query to first 200 words. Inform user: "Your query was trimmed to 200 words for best results." | 🟢 |

### 5.4 — LLM Rate Limiting & Budget Edge Cases

| ID | Scenario | Trigger | Impact | Detection | Handling | Severity |
|---|---|---|---|---|---|---|
| EC-5.22 | **Gemini RPM limit hit (15 req/min)** | Concurrent users or rapid-fire queries | HTTP 429 from Gemini API | `status_code == 429` or `ResourceExhausted` error | Exponential backoff (1s → 2s → 4s → 8s, max 60s). If still failing after 5 retries, fall back to Ollama. Return response with a note about delay. | 🟡 |
| EC-5.23 | **Gemini daily limit hit (1,500 req/day)** | Heavy pipeline run + many RAG queries in one day | All Gemini calls fail for the rest of the day | Daily request counter exceeds 1,500 | Switch to Ollama for the remainder of the day. Log: "Gemini daily quota exhausted. Using local model." Cache aggressively to minimize calls. | 🟡 |
| EC-5.24 | **Ollama is not installed or not running** | User doesn't have Ollama set up; it's the fallback but unavailable | No LLM available at all | `ConnectionRefusedError` when calling `localhost:11434` | Return error: "LLM service unavailable. Both Gemini quota and Ollama are unavailable. Please wait for Gemini quota reset or install Ollama." Pipeline halts gracefully. | 🔴 |
| EC-5.25 | **Token estimation is significantly wrong** | `tiktoken` estimation doesn't match Gemini's actual tokenizer | Budget check says OK but actual call is rejected for exceeding context | Gemini returns 400 with token limit error | Add a 20% safety margin to token estimates. If rejected, reduce context (drop the lowest-ranked snippet) and retry. | 🟡 |
| EC-5.26 | **Cache produces stale results** | Corpus was re-indexed but cache still holds answers from old corpus | Answers reference chunks that no longer exist | Cached response `chunk_ids` don't exist in current vector store | Invalidate RAG generation cache whenever the vector store is rebuilt. Key cache entries by `(query_hash, index_version)` not just `query_hash`. | 🟡 |

---

## Stage 6: Reports & Verification

| ID | Scenario | Trigger | Impact | Detection | Handling | Severity |
|---|---|---|---|---|---|---|
| EC-6.01 | **Opportunity report exceeds reasonable length** | Many themes with extensive evidence | Report becomes unwieldy (>50 pages) | `word_count > 15,000` | Cap evidence quotes to top 3 per theme in the report body. Move full evidence to an appendix. Keep executive summary under 500 words. | 🟢 |
| EC-6.02 | **Report markdown has broken rendering** | Unescaped special characters in theme names or evidence (e.g., `|`, `#`, `*`) | Report renders incorrectly in Next.js viewer | Markdown parser warnings; visual inspection shows broken formatting | Escape special markdown characters in theme names and evidence snippets: `|` → `\|`, `#` → `\#`, etc. | 🟢 |
| EC-6.03 | **Privacy log shows zero PII stripped** | Either (a) no PII existed, or (b) PII stripper didn't work | Ambiguous — is the pipeline working or is it broken? | All PII counts = 0 | If the raw corpus has > 100 records and zero PII is found, run a manual spot-check on 10 random records. It's possible no PII exists (app store reviews often don't have handles), but verify. | 🟢 |
| EC-6.04 | **Final PII sweep finds PII in output files** | PII stripper missed something | Compliance violation | `grep` regex matches in `data/` or `reports/` | HALT deployment. Fix the PII stripper. Re-run Phase 2 and all downstream phases. Document the incident. | 🔴 |

---

## Cross-Cutting: Deployment (Vercel + Railway)

| ID | Scenario | Trigger | Impact | Detection | Handling | Severity |
|---|---|---|---|---|---|---|
| EC-D.01 | **Railway free-tier credit exhausted** | $5/month credit used up | Backend goes offline | Railway dashboard shows $0 remaining; API returns 503 | Monitor credit usage. Set up Railway budget alerts. If exhausted, serve a static "Service temporarily unavailable" page. | 🔴 |
| EC-D.02 | **Railway cold start latency** | Container sleeps after inactivity; first request takes 10–30s | First user experiences very slow response | Response time > 10s on first request after idle | Add a health check endpoint that Railway pings to keep the container warm. Document expected cold start. Frontend: show a "Warming up..." indicator. | 🟡 |
| EC-D.03 | **Railway container runs out of memory** | Loading BGE-small + reranker + ChromaDB + FastAPI exceeds free-tier RAM | Container crashes with OOM | Railway logs show `Killed` or `OOMKilled` | Profile memory usage locally first. BGE-small (~100MB) + reranker (~80MB) + ChromaDB index + FastAPI should fit in 512MB. If not, load models lazily (only when first query arrives). Consider FAISS instead of ChromaDB for lower memory. | 🔴 |
| EC-D.04 | **Vercel build fails** | TypeScript errors, missing dependencies, or Next.js version mismatch | Frontend is not deployed | Vercel build logs show errors | Fix locally first (`npm run build`). Pin dependency versions in `package.json`. Test build before deploying. | 🟡 |
| EC-D.05 | **CORS mismatch between Vercel and Railway** | Frontend URL not in Railway's CORS allowlist | All frontend API calls fail with CORS error | Browser console shows `Access-Control-Allow-Origin` error | Add both `https://myntra-discovery.vercel.app` AND `http://localhost:3000` to CORS origins. Use environment variables for production URLs. | 🔴 |
| EC-D.06 | **Railway URL changes after redeployment** | Railway regenerates the app URL | Frontend points to old backend URL | API calls return 404 or connection refused | Use Railway's custom domain feature or stable URL. Update `NEXT_PUBLIC_API_URL` on Vercel whenever Railway URL changes. | 🟡 |
| EC-D.07 | **SSE streaming doesn't work through Vercel proxy** | Vercel's edge network may buffer/interfere with SSE | Streaming responses arrive as a single dump instead of incrementally | Frontend receives all text at once instead of token-by-token | Set `Transfer-Encoding: chunked` headers. If Vercel buffers SSE, switch to polling-based approach or WebSocket. Test streaming in production before launch. | 🟡 |
| EC-D.08 | **ChromaDB persistence on Railway restart** | Railway containers are ephemeral; data on disk may be lost on restart | Vector store is wiped; queries fail | ChromaDB returns empty collections after restart | Use Railway's persistent volume feature. Alternatively, rebuild the index on startup if the vectorstore directory is empty (slower but self-healing). | 🔴 |

---

## Cross-Cutting: Data Integrity

| ID | Scenario | Trigger | Impact | Detection | Handling | Severity |
|---|---|---|---|---|---|---|
| EC-X.01 | **Pipeline stage is run out of order** | User runs `--analyze` before `--clean` | Stage reads missing input files | `FileNotFoundError` for expected input | Each stage checks entry criteria before starting. If input files don't exist, error with: "Phase X requires [file]. Run Phase Y first." | 🟡 |
| EC-X.02 | **Input file is corrupted (invalid JSONL)** | Disk error, interrupted write, or manual editing | Stage crashes on `json.loads()` | `json.JSONDecodeError` on a specific line | Read JSONL line-by-line. Skip corrupted lines. Log: "Skipped N corrupted lines in {file}." If > 10% lines are corrupted, abort with ERROR. | 🟡 |
| EC-X.03 | **Disk space runs out mid-pipeline** | Large corpus + multiple intermediate files | Writes fail silently or partially | `OSError: No space left on device` | Check available disk space before each stage. Warn if < 500MB free. Clean up intermediate files from previous runs if needed. | 🔴 |
| EC-X.04 | **Pipeline is interrupted mid-stage (Ctrl+C, crash)** | User interrupts, power failure, or OOM kill | Partial output files that look complete | Output file exists but is truncated | Use atomic writes: write to a `.tmp` file, then rename to final name on completion. Check file integrity (valid JSONL, expected schema) at stage entry. | 🟡 |
| EC-X.05 | **Concurrent pipeline runs** | Two terminals both run `python pipeline.py --all` | Race conditions on file writes; corrupted output | File locking check or PID file | Use a lockfile (`data/.pipeline.lock`). If lock exists, abort with: "Another pipeline run is in progress." | 🟡 |
| EC-X.06 | **`.env` file is missing or has empty API keys** | User forgot to configure, or copied `.env.example` without filling in values | API calls fail with auth errors | `GEMINI_API_KEY` is empty string or `None` | Validate all required env vars at startup (Phase 0 smoke test). Error with clear message: "GEMINI_API_KEY is not set in .env. See .env.example." | 🔴 |

---

## Cross-Cutting: LLM-Specific

| ID | Scenario | Trigger | Impact | Detection | Handling | Severity |
|---|---|---|---|---|---|---|
| EC-L.01 | **Gemini model version is deprecated** | Google deprecates `gemini-1.5-flash` | API calls fail with 404 or deprecation error | HTTP 404 or explicit deprecation warning in response | Make model name configurable in `.env`. Update to the latest model. Log deprecation warnings prominently. | 🟡 |
| EC-L.02 | **Gemini returns different JSON structure across calls** | Non-deterministic formatting (sometimes nested, sometimes flat) | Downstream parsers break on unexpected structure | Schema validation fails intermittently | Use structured output (Gemini's JSON mode) if available. If not, write robust parsers that handle common variations. Normalize before processing. | 🟡 |
| EC-L.03 | **Ollama model not downloaded** | User configured `LLM_PROVIDER=ollama` but didn't `ollama pull llama3` | All LLM calls fail | `ollama.ResponseError: model not found` | Check on startup: `ollama list` and verify the configured model exists. If not, prompt user to run `ollama pull {model}`. | 🟡 |
| EC-L.04 | **Ollama is too slow for batch analysis** | Local hardware is underpowered (no GPU, limited RAM) | Phase 3 takes hours or days instead of minutes | Processing rate < 1 batch/minute | Log estimated completion time. Allow user to switch to Gemini mid-run. Consider reducing batch count by sampling the corpus. | 🟢 |
| EC-L.05 | **LLM cache grows unbounded** | Months of pipeline runs without cache cleanup | Disk space consumed by stale cache files | `du -sh data/themes/.cache/` returns > 1GB | Add a cache eviction policy: delete entries older than 30 days. Add a `make clean-cache` target. | 🟢 |

---

## Retrieval Evaluation Edge Cases

| ID | Scenario | Trigger | Impact | Detection | Handling | Severity |
|---|---|---|---|---|---|---|
| EC-E.01 | **Benchmark queries have no labeled relevant chunks yet** | Phase 2 hasn't run, so `expected_chunks` in benchmark are placeholder `"..."` | Evaluation metrics are meaningless | All expected_chunks are `"..."` or empty | Skip evaluation with INFO log: "Benchmark not yet labeled. Run after Phase 2 and label relevant chunks." | 🟢 |
| EC-E.02 | **Recall@5 is below target (< 0.70)** | Embedding model or chunking strategy isn't effective | Poor retrieval quality → poor RAG answers | Benchmark results show Recall@5 < 0.70 | Investigate: (a) Are chunks too long/short? Adjust chunk size. (b) Is query prefix correct? (c) Try BGE-base instead of BGE-small. (d) Verify index was built correctly. | 🟡 |
| EC-E.03 | **Reranker shows negative lift** | Reranker makes results WORSE than BGE-only | Wasted computation + degraded quality | `reranker_lift` is negative | Disable reranker (`RERANKER_ENABLED = False`). Log the finding. Consider a different reranker model. | 🟡 |
| EC-E.04 | **Hindi/Hinglish queries score 0.0 across all metrics** | BGE-small has very poor cross-lingual capability | Hindi-speaking users get no useful results | All Hindi/Hinglish Recall@K = 0.0 | Implement query translation (Hindi → English) as a pre-processing step. Use Gemini for translation (it's a single short API call). | 🟡 |

---

## Summary: Severity Distribution

| Severity | Count | What to Prioritize |
|---|---|---|
| 🔴 **Critical** | 16 | Must be handled before launch. Pipeline halts or data integrity is compromised. |
| 🟡 **Medium** | 40 | Should be handled. Pipeline degrades gracefully but output quality suffers. |
| 🟢 **Low** | 21 | Nice to handle. Minor annoyances or unlikely scenarios. |
| **Total** | **77** | |

### Top 10 Must-Handle Edge Cases

| Rank | ID | Scenario | Why Critical |
|---|---|---|---|
| 1 | EC-2.01 | Hinglish PII leakage | Compliance risk — PII in output |
| 2 | EC-5.14 | Zero citations in RAG answer | Violates core traceability principle |
| 3 | EC-5.15 | Hallucinated chunk_ids | False evidence trail |
| 4 | EC-D.05 | CORS mismatch | Entire frontend is broken |
| 5 | EC-D.08 | ChromaDB lost on Railway restart | Queries fail post-restart |
| 6 | EC-3.03 | Hallucinated chunk_ids in themes | False evidence in report |
| 7 | EC-6.04 | PII found in final sweep | Compliance violation |
| 8 | EC-X.06 | Missing API keys | Everything fails at startup |
| 9 | EC-1.08 | Myntra blocks scraping | Zero product reviews |
| 10 | EC-D.03 | Railway OOM | Backend crashes |
