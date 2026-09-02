# Architecture: AI-Powered Wishlist-to-Purchase Discovery Engine

> **Source:** Derived from [context.md](file:///Users/daniamacbook/Desktop/NL%20Myntra/Docs/context.md)
> **Scope:** Discovery layer only — ingestion through RAG. Solution design is explicitly out of scope.

---

## 1. System Overview

The Discovery Engine is a five-stage, offline-first pipeline that converts scattered public conversations about fashion wishlisting into a ranked, evidence-backed opportunity map. It is designed to answer **ten research questions** posed by the Myntra Growth team, with every claim traceable to real user snippets.

```mermaid
flowchart LR
    A["1. Data Sourcing\n& Ingestion"] --> B["2. Cleaning &\nNormalization"]
    B --> C["3. Thematic\nAnalysis Engine"]
    C --> D["4. Opportunity\nQuantification"]
    D --> E["5. RAG\nAssistant"]

    style A fill:#1e3a5f,stroke:#4a90d9,color:#fff
    style B fill:#2d4a22,stroke:#6abf4b,color:#fff
    style C fill:#5c3d1e,stroke:#d4943a,color:#fff
    style D fill:#4a1942,stroke:#b44ad9,color:#fff
    style E fill:#1a4a4a,stroke:#4ad4d9,color:#fff
```

### Design Principles

| Principle | Rationale |
|---|---|
| **Local-first, zero-cost** | All processing runs locally; LLMs via free-tier APIs or local Ollama; no paid proxies, hosting, or vector databases |
| **Token efficiency** | Summarize/compress before repeated LLM calls; cache intermediates; never re-process raw text |
| **PII-free pipeline** | Usernames, emails, device IDs stripped before storage — nothing identifying reaches any output |
| **Evidence traceability** | Every theme and RAG answer links back to ≥1 real, anonymized source snippet |
| **ToS-respecting collection** | Public sources only; no login-gated scraping; respect rate limits and robots.txt |

---

## 2. High-Level Architecture Diagram

```mermaid
graph TB
    subgraph Sources["Data Sources"]
        S1["App Store Reviews"]
        S2["Play Store Reviews"]
        S3["Reddit Threads\n& Comments"]
        S4["Quora Answers"]
        S5["YouTube Comments\n(Haul/Review/Try-on)"]
        S6["Fashion Forums\n& Communities"]
        S7["Myntra Product\nReviews & Q&A"]
        S8["Instagram Comments\n& Threads"]
        S9["User Research\n(Interviews & Surveys)"]
    end

    subgraph Ingestion["Stage 1: Ingestion Layer"]
        I1["Platform-Specific\nScraper Modules"]
        I2["Rate Limiter\n& ToS Guard"]
        I3["Raw Data Store\n(JSON/CSV on disk)"]
    end

    subgraph Cleaning["Stage 2: Cleaning & Normalization"]
        C1["PII Stripper"]
        C2["Deduplicator"]
        C3["Spam & Boilerplate\nFilter"]
        C4["Relevance Filter"]
        C5["Chunker\n(long-form → units)"]
        C6["Clean Corpus Store\n(JSON/CSV on disk)"]
    end

    subgraph Analysis["Stage 3: Thematic Analysis"]
        T1["LLM Theme Extraction\n(batch, cached)"]
        T2["Theme Consolidation\n& Dedup"]
        T3["Research Question\nMapping"]
        T4["Theme Registry\n(JSON on disk)"]
    end

    subgraph Quant["Stage 4: Quantification & Prioritization"]
        Q1["Frequency Counter"]
        Q2["Platform Spread\nScorer"]
        Q3["Purchase-Delay\nRelevance Scorer"]
        Q4["Segment Slicer"]
        Q5["Opportunity Matrix\nGenerator"]
    end

    subgraph RAG["Stage 5: RAG Assistant"]
        R1["BGE Embedder\n(BAAI/bge-base-en-v1.5)"]
        R2["Vector Store\n(ChromaDB / FAISS)"]
        R3["Top-K Retriever"]
        R4["LLM Answer Generator\n(with citation)"]
        R5["Next.js Frontend\n(Vercel)"]
        R6["FastAPI Backend\n(Railway)"]
    end

    subgraph Outputs["Deliverables"]
        O1["Thematic Opportunity\nReport"]
        O2["Segment-Cut View"]
        O3["Data & Privacy Log"]
        O4["README"]
    end

    Sources --> I1
    I1 --> I2 --> I3
    I3 --> C1 --> C2 --> C3 --> C4 --> C5 --> C6
    C6 --> T1 --> T2 --> T3 --> T4
    T4 --> Q1 & Q2 & Q3
    Q1 & Q2 & Q3 --> Q4 --> Q5
    Q5 --> O1 & O2
    C6 --> R1 --> R2
    T4 --> R2
    R2 --> R3 --> R4 --> R5
    C1 -.-> O3
```

---

## 3. Pipeline Stages — Detailed Design

### 3.1 Stage 1: Data Sourcing & Ingestion

**Purpose:** Collect raw public conversations and first-party research data about fashion wishlisting, shortlisting, and purchase decisions from multiple platforms and research channels.

#### 3.1.1 Source Modules

Each platform gets a dedicated scraper module. All scraped-source modules implement a shared interface. First-party research data (interviews & surveys) uses a file-based ingestion module.

```
Interface: SourceScraper
├── configure(query_terms, recency_window, max_results)
├── fetch() → List[RawRecord]
├── get_rate_limit_status() → RateLimitInfo
└── export(path) → void

Interface: ResearchIngester
├── load(file_path) → List[RawRecord]
├── validate_schema() → bool
└── export(path) → void
```

| Source | Method | Free-Tier Tool / Approach | Recency Window |
|---|---|---|---|
| **App Store Reviews** | Apify free-tier actor or `app-store-scraper` npm | Apify (free tier: 30 actor-seconds/month) | Last 6–12 months |
| **Play Store Reviews** | Apify free-tier actor or `google-play-scraper` | Apify / Python library | Last 6–12 months |
| **Reddit** | Apify Reddit scraper actors (free tier) | `trudax--reddit-scraper-lite`, `automation-lab--reddit-scraper` | Last 6–12 months |
| **Quora** | Apify Quora scraper actors (free tier) | `fatihtahta--quora-scraper`, `crawlerbros--quora-search-scraper` | Last 6–12 months |
| **YouTube Comments** | Apify YouTube scraper + YouTube Data API v3 (free tier) | `streamers--youtube-scraper`, YouTube Data API v3 (10,000 units/day free) | Last 6–12 months |
| **Instagram** | Apify Instagram scraper (free tier) | `apify--instagram-scraper` | Last 6–12 months |
| **Myntra Product Reviews** | Apify web scraper or custom scraper | Apify / `requests` + `bs4` (public product pages) | Last 6–12 months |
| **Fashion Forums** | Lightweight HTTP scraping + BeautifulSoup | Python `requests` + `bs4` | Last 6–12 months |
| **User Interviews** | File-based ingestion (JSON/CSV) | Manual transcripts pre-loaded to `data/research/interviews/` | N/A (existing data) |
| **User Surveys** | File-based ingestion (JSON/CSV) | Survey exports pre-loaded to `data/research/surveys/` | N/A (existing data) |

#### 3.1.2 Search Query Strategy

Queries are designed to surface wishlist/purchase-intent conversations:

```
Primary terms:
  "myntra wishlist", "myntra shortlist", "myntra cart abandon",
  "myntra not buying", "myntra save for later", "myntra hesitate",
  "online fashion wishlist", "fashion shopping cart",
  "ajio wishlist", "fashion app wishlist"

Extended terms (for Reddit/Quora):
  "why I don't buy from wishlist", "fashion purchase decision",
  "online shopping indecision", "saved items never bought",
  "wishlist vs actually buying", "fashion try before buy"
```

#### 3.1.3 Raw Data Schema

Every ingested record conforms to this schema before cleaning:

```json
{
  "record_id": "uuid-v4",
  "source_platform": "reddit | quora | appstore | playstore | youtube | instagram | forum | myntra_reviews | interview | survey",
  "source_url": "https://... (or null for research data)",
  "text": "raw text content",
  "timestamp": "ISO-8601",
  "ingestion_timestamp": "ISO-8601",
  "source_type": "scraped | first_party_research",
  "metadata": {
    "subreddit": "optional",
    "thread_title": "optional",
    "rating": "optional (for app/product reviews)",
    "video_title": "optional (for YouTube)",
    "product_category": "optional (for Myntra reviews)",
    "product_name": "optional (for Myntra reviews)",
    "interview_id": "optional (for interviews, anonymized)",
    "survey_question": "optional (for surveys)"
  }
}
```

> **PII rule:** No `username`, `author`, `email`, `device_id`, or `account_id` fields — ever. For user research data, interviewee identifiers must be anonymized (e.g., P01, P02) before ingestion.

#### 3.1.4 Rate Limiting & ToS Guard

- Per-platform configurable rate limits (requests/minute, requests/day)
- Exponential backoff on HTTP 429 / 503
- robots.txt check before forum scraping
- All Apify calls route through the free-tier quota tracker

#### 3.1.5 Storage

- **Format:** JSONL files, one per platform per run (`raw/reddit_2026-08.jsonl`, `raw/myntra_reviews_2026-08.jsonl`, `raw/interviews.jsonl`, `raw/surveys.jsonl`)
- **Location:** Local disk — no cloud storage
- **Estimated volume:** 8,000–30,000 raw records across all sources (including research data)

---

### 3.2 Stage 2: Cleaning & Normalization

**Purpose:** Transform raw records into a de-identified, deduplicated, relevance-filtered corpus ready for LLM analysis.

#### 3.2.1 Processing Pipeline

```mermaid
flowchart LR
    Raw["Raw JSONL"] --> PII["PII Stripper"]
    PII --> Dedup["Deduplicator\n(fuzzy hash)"]
    Dedup --> Spam["Spam/Boilerplate\nFilter"]
    Spam --> Relevance["Relevance\nClassifier"]
    Relevance --> Chunk["Chunker"]
    Chunk --> Clean["Clean Corpus\nJSONL"]

    style Raw fill:#333,stroke:#666,color:#fff
    style Clean fill:#1a4a1a,stroke:#4ad94a,color:#fff
```

| Step | Technique | Details |
|---|---|---|
| **PII Stripping** | Regex + spaCy NER | Remove `@handles`, emails, phone numbers, names detected by NER. Log what was stripped (counts only, not content) for the privacy log. |
| **Deduplication** | MinHash / SimHash | Near-duplicate detection at 85% similarity threshold. Cross-platform dedup to avoid counting the same copypasted review twice. |
| **Spam / Boilerplate** | Rule-based + heuristic | Remove reviews < 10 words, repetitive "5 stars great app" boilerplate, promotional content, non-English text (unless Hindi/Hinglish — retain for Indian fashion context). |
| **Relevance Filter** | Keyword + lightweight LLM classifier | Keep only records that discuss wishlisting, purchase decisions, fashion shopping friction, comparison behavior, or fit/size/price concerns. Discard pure delivery/logistics complaints unless they connect to purchase hesitation. |
| **Chunking** | Sliding window, semantic boundaries | Reddit threads: split into individual comment-level chunks. YouTube: split comment sections by comment. Long reviews: split at ~300 tokens with 50-token overlap. Each chunk retains its parent `record_id`. |

#### 3.2.2 Clean Corpus Schema

```json
{
  "chunk_id": "uuid-v4",
  "parent_record_id": "uuid-v4",
  "source_platform": "reddit",
  "text": "cleaned, PII-free text",
  "word_count": 87,
  "timestamp": "ISO-8601",
  "relevance_tags": ["wishlist_intent", "price_comparison"],
  "language": "en"
}
```

#### 3.2.3 Storage

- **Format:** JSONL (`clean/corpus.jsonl`)
- **Expected volume after cleaning:** 3,000–12,000 chunks
- **Privacy log:** Auto-generated counts of PII fields stripped, records filtered, and reasons

---

### 3.3 Stage 3: Thematic Analysis Engine

**Purpose:** Use an LLM to extract emergent themes from the corpus, mapping each to the 10 research questions, with verbatim evidence.

#### 3.3.1 Two-Pass Architecture

The analysis uses a **map-reduce** approach to stay within free-tier token limits:

```mermaid
flowchart TB
    subgraph Pass1["Pass 1: Map — Micro-Theme Extraction"]
        B1["Batch of ~20 chunks"] --> LLM1["LLM Call:\nExtract micro-themes\n+ assign research Qs"]
        LLM1 --> MT["Micro-themes\n(~50–200)"]
    end

    subgraph Pass2["Pass 2: Reduce — Theme Consolidation"]
        MT --> LLM2["LLM Call:\nMerge similar micro-themes\ninto macro-themes"]
        LLM2 --> FT["Final Themes\n(~10–25)"]
    end

    subgraph Enrichment["Enrichment"]
        FT --> Map["Map verbatim\nsnippets to themes"]
        Map --> Count["Count frequency\n& source spread"]
        Count --> RQ["Link to research\nquestions"]
    end

    style Pass1 fill:#1e1e2e,stroke:#4a90d9,color:#fff
    style Pass2 fill:#1e1e2e,stroke:#d4943a,color:#fff
    style Enrichment fill:#1e1e2e,stroke:#6abf4b,color:#fff
```

**Pass 1 — Micro-Theme Extraction (Map):**
- Batch chunks into groups of ~20 (to fit within context window)
- For each batch, prompt the LLM to extract micro-themes, assign relevant research question IDs (RQ1–RQ10), and select the most representative verbatim quote per theme
- Cache each batch result to avoid re-processing

**Pass 2 — Theme Consolidation (Reduce):**
- Feed all micro-themes to the LLM in a single consolidation prompt
- Merge semantically overlapping micro-themes into macro-themes (target: 10–25 final themes)
- Produce a canonical name, description, and merged evidence list for each

#### 3.3.2 Theme Schema

```json
{
  "theme_id": "T-001",
  "name": "Size & Fit Uncertainty",
  "description": "Users hesitate to purchase because...",
  "research_questions": ["RQ3", "RQ7"],
  "evidence": [
    {
      "chunk_id": "uuid",
      "snippet": "I really wanted to buy the dress but...",
      "source_platform": "reddit"
    }
  ],
  "micro_theme_ids": ["MT-003", "MT-017", "MT-042"],
  "chunk_count": 187,
  "source_platforms": ["reddit", "appstore", "youtube"],
  "platform_distribution": {
    "reddit": 92,
    "appstore": 54,
    "youtube": 41
  }
}
```

#### 3.3.3 Token Efficiency Strategy

| Technique | Saving |
|---|---|
| Batch chunking (20 chunks/call) | Reduces API calls by ~95% vs. per-chunk |
| Intermediate caching (JSONL on disk) | Zero re-processing on re-runs |
| Compression prompt ("extract themes only, no preamble") | ~30% token reduction per response |
| Two-pass map-reduce vs. single mega-prompt | Stays within free-tier context limits |

---

### 3.4 Stage 4: Opportunity Quantification & Prioritization

**Purpose:** Score and rank themes into a stakeholder-ready opportunity matrix.

#### 3.4.1 Scoring Dimensions

Each theme is scored on three axes:

| Dimension | Signal | Calculation |
|---|---|---|
| **Frequency** | How often this friction appears | `chunk_count / total_corpus_chunks` normalized to 0–100 |
| **Platform Spread** | Cross-platform corroboration | `unique_platforms / total_platforms` normalized to 0–100 |
| **Purchase-Delay Relevance** | How directly it maps to abandonment/postponement | LLM-scored 0–100 (prompt: "How directly does this theme explain why a user would NOT convert a wishlisted item?") |

**Composite Opportunity Score:**

```
opportunity_score = (0.4 × frequency) + (0.3 × platform_spread) + (0.3 × purchase_delay_relevance)
```

#### 3.4.2 Opportunity Matrix Schema

```json
{
  "theme_id": "T-001",
  "name": "Size & Fit Uncertainty",
  "frequency_score": 78,
  "platform_spread_score": 83,
  "purchase_delay_score": 91,
  "opportunity_score": 83.5,
  "rank": 1,
  "research_questions": ["RQ3", "RQ7"],
  "segment_cuts": {
    "category": { "women_western": 62, "men_casual": 18 },
    "price_band": { "under_1000": 34, "1000_3000": 41, "above_3000": 25 },
    "occasion": { "everyday": 55, "occasion_specific": 45 }
  }
}
```

#### 3.4.3 Segment Slicing

Where corpus volume allows, themes are broken out by inferred segments:

- **Product category** — extracted from mentions (e.g., "kurta", "sneakers", "dress")
- **Price band** — parsed from price mentions (₹ amounts, "expensive", "budget")
- **Occasion vs. everyday** — classified by context cues ("wedding", "office", "daily wear")
- **User type** — first-time vs. repeat buyer signals ("never ordered from Myntra" vs. "I always wishlist first")

> **Minimum sample-size rule:** Segment inference is best-effort from text. A segment is only reported if it has **≥10 supporting chunks**. Segments below this threshold are flagged as `low_confidence` and excluded from the main report to avoid spurious conclusions from thin data.

---

### 3.5 Stage 5: Lightweight RAG Assistant

**Purpose:** Let stakeholders ask free-form questions against the corpus and theme summaries, with every answer grounded in and cited back to source snippets.

#### 3.5.1 Architecture

```mermaid
flowchart LR
    User["User Query\n(Next.js on Vercel)"] --> API["FastAPI Backend\n(Railway)"]
    API --> Embed["BGE-small Query\nEmbedding"]
    Embed --> Retrieve["Vector Retrieval\n(top 15–20)"]
    Retrieve --> Rerank["Cross-Encoder\nReranker"]
    Rerank --> Top["Top 5–8\nSnippets"]
    Top --> Context["Build Context\nWindow"]
    Context --> Budget["Token Budget\nCheck"]
    Budget --> LLM["Gemini / Ollama\nGeneration"]
    LLM --> Validate["Citation\nValidation"]
    Validate --> API
    API --> User

    VStore[("Vector Store\n(ChromaDB / FAISS)")] --> Retrieve

    style User fill:#1a4a4a,stroke:#4ad4d9,color:#fff
    style API fill:#3a1a4a,stroke:#b44ad9,color:#fff
    style VStore fill:#2d2d4a,stroke:#9a9ad9,color:#fff
    style Rerank fill:#4a3a1a,stroke:#d9a44a,color:#fff
    style Validate fill:#1a4a1a,stroke:#4ad94a,color:#fff
```

#### 3.5.2 Deployment Architecture

```mermaid
flowchart TB
    subgraph Vercel["Vercel (Frontend)"]
        FE["Next.js App\nChat UI + Report Viewer"]
    end

    subgraph Railway["Railway (Backend)"]
        BE["FastAPI Server"]
        VS[("ChromaDB\nVector Store")]
        EMB["BGE Embedder"]
    end

    FE <-->|"REST API / SSE"| BE
    BE --> EMB
    BE --> VS
    BE -->|"Gemini API"| LLM["LLM"]

    style Vercel fill:#000,stroke:#fff,color:#fff
    style Railway fill:#1a1a3a,stroke:#6a6ad9,color:#fff
```

| Component | Platform | URL Pattern | Free Tier |
|---|---|---|---|
| **Frontend** | Vercel | `https://myntra-discovery.vercel.app` | ✅ Hobby plan (free) |
| **Backend** | Railway | `https://myntra-discovery-api.up.railway.app` | ✅ Trial plan ($5 credit/month) |

#### 3.5.3 Index Construction

Two collections in the vector store:

| Collection | Contents | Chunk Size | Count |
|---|---|---|---|
| `corpus_chunks` | Cleaned user conversation chunks (scraped + research) | ~300 tokens | 5,000–20,000 |
| `theme_summaries` | Theme descriptions + top evidence snippets | ~500 tokens | 10–25 |

#### 3.5.4 Embedding Model

- **Model:** `BAAI/bge-small-en-v1.5` (via `sentence-transformers`) — free, open-source, local, no API cost
- **Dimension:** 384
- **Runs on:** CPU (no GPU required)
- **Why BGE-small:** Best trade-off of retrieval accuracy vs. memory/speed for a local-first, free-tier setup. Outperforms MiniLM on MTEB benchmarks while remaining lightweight enough for Railway's free tier. Instruction-aware embeddings improve domain-specific queries.
- **Configurable:** Model name, query instruction prefix, and batch size are all configurable via `backend/src/rag/rag_config.py`

#### 3.5.5 Reranker

- **Model:** `cross-encoder/ms-marco-MiniLM-L-6-v2` (via `sentence-transformers`) — free, local, no API cost
- **Purpose:** Re-score the top 15–20 BGE candidates using a cross-encoder for higher precision before sending to the LLM
- **Runs on:** CPU
- **Configurable:** Reranker model, candidate pool size, and final top-K are all configurable

#### 3.5.6 Retrieval & Generation Pipeline

The full RAG flow per query:

```
Query
  → BGE-small embedding (with instruction prefix)
  → Vector retrieval: top 15–20 candidates from both collections
  → Cross-encoder rerank: score all candidates with ms-marco-MiniLM
  → Select top 5–8 by reranker score
  → Build context window (with token budget check)
  → Gemini / Ollama generation (with token estimation + rate limiting)
  → Citation validation (every claim must have [Source: ...] tag)
  → Return cited answer
```

| Parameter | Value | Configurable | Rationale |
|---|---|---|---|
| **Initial retrieval K** | 15–20 | ✅ `rag_config.py` | Wide net for recall before reranking |
| **Final top-K (post-rerank)** | 5–8 | ✅ `rag_config.py` | Precision-focused context for LLM |
| **Retrieval scope** | Both collections | ✅ | Corpus for raw evidence, themes for synthesized context |
| **Reranker model** | `cross-encoder/ms-marco-MiniLM-L-6-v2` | ✅ `rag_config.py` | Free, local, strong reranking accuracy |
| **LLM generation** | Gemini free tier / Ollama (local) | ✅ `.env` | System prompt enforces citation format |
| **Citation format** | `[Source: Reddit, chunk_id: abc123]` | — | Every claim links to a retrievable snippet |
| **Citation validation** | Post-generation check: every factual sentence must have ≥1 `[Source:]` tag; responses without citations are rejected and retried once | — | Prevents unsupported claims |
| **Hallucination guard** | System prompt: "Only answer from retrieved context. If insufficient evidence, say so." | — | Prevents unsupported claims |

#### 3.5.7 LLM Call Protocol

Before **every** Gemini API call (in both analysis and RAG generation):

```
1. Estimate input tokens (tiktoken / char-based approximation)
2. Check requests-per-minute budget (Gemini free tier: 15 RPM)
3. Check daily request budget (Gemini free tier: 1,500 RPD)
4. If budget exceeded → queue or fall back to Ollama
5. On HTTP 429 → exponential backoff (1s, 2s, 4s, 8s, max 60s)
6. Cache result keyed by hash(prompt + system_prompt)
7. On cache hit → skip API call entirely
8. Retry only on transient errors (429, 503), NOT on 400/invalid
```

This protocol is enforced by `src/utils/llm_client.py` — no module calls Gemini directly.

#### 3.5.8 Retrieval Evaluation

A benchmark suite of **20–30 test queries** (covering English, Hindi, and Hinglish) is used to evaluate retrieval quality before and after reranking:

| Metric | Target | Measured Against |
|---|---|---|
| **Recall@5** | ≥0.70 | Pre-labeled relevant chunks for each query |
| **Recall@10** | ≥0.85 | Pre-labeled relevant chunks for each query |
| **MRR (Mean Reciprocal Rank)** | ≥0.60 | First relevant chunk position |
| **Reranker lift** | ≥10% Recall@5 improvement over BGE-only | Before/after reranking comparison |

**Benchmark query categories:**
- 10 English queries (direct RQ-mapped)
- 5 Hindi queries (e.g., "myntra pe wishlist mein kyun rakhte ho?")
- 5 Hinglish queries (e.g., "why myntra ki wishlist se kuch nahi khareedta")
- 5–10 edge cases (out-of-scope, ambiguous, multi-theme)

Results are saved to `data/eval/retrieval_benchmark.json` and logged to `reports/retrieval_eval.md`.

#### 3.5.9 Frontend (Next.js on Vercel)

| Feature | Details |
|---|---|
| **Chat interface** | Real-time Q&A with streaming responses (SSE) |
| **Report viewer** | Renders `opportunity_report.md` and `segment_view.md` as interactive pages |
| **Source explorer** | Click on citations to view full source snippets |
| **Example queries** | Pre-loaded question suggestions for quick start |
| **Responsive design** | Mobile-friendly for stakeholder access |

#### 3.5.10 Backend (FastAPI on Railway)

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/query` | POST | Accept user query, run retrieve → rerank → generate → validate pipeline |
| `/api/themes` | GET | Return all themes with scores and evidence |
| `/api/matrix` | GET | Return opportunity matrix data |
| `/api/report` | GET | Return the full opportunity report |
| `/api/health` | GET | Health check + LLM quota status |

---

## 4. Technology Stack

All tools are free-tier or open-source. Deployment uses Vercel (frontend) and Railway (backend) free tiers.

| Layer | Technology | Cost |
|---|---|---|
| **Backend Language** | Python 3.10+ | Free |
| **Frontend Language** | TypeScript / Next.js | Free |
| **Scraping / Ingestion** | Apify free tier (actors), `requests`, `BeautifulSoup` | Free (within quotas) |
| **YouTube Data API v3** | `google-api-python-client` | Free (10,000 units/day) |
| **User Research Ingestion** | File-based loader (JSON/CSV) | Free |
| **Myntra Reviews** | Apify / custom scraper | Free (within quotas) |
| **PII Detection** | Regex + spaCy (`en_core_web_sm`) | Free |
| **Deduplication** | `datasketch` (MinHash) | Free |
| **LLM — Analysis** | Google Gemini API (free tier) / Ollama (local fallback) | Free |
| **LLM — RAG Generation** | Google Gemini API (free tier) / Ollama (local fallback) | Free |
| **Embeddings** | `BAAI/bge-small-en-v1.5` (via `sentence-transformers`) | Free, local |
| **Reranker** | `cross-encoder/ms-marco-MiniLM-L-6-v2` (via `sentence-transformers`) | Free, local |
| **Vector Store** | ChromaDB (local / Railway) or FAISS | Free |
| **Frontend Hosting** | Vercel (Hobby plan) | Free |
| **Backend Hosting** | Railway (Trial plan) | Free ($5 credit/month) |
| **Backend Framework** | FastAPI | Free |
| **Data Storage** | Local JSONL files on disk / Railway volume | Free |
| **Orchestration** | Python scripts / Makefile | Free |
| **Reporting** | Markdown / Next.js rendered pages | Free |

---

## 5. Project Directory Structure

```
NL Myntra/
├── Docs/
│   ├── context.md                  # Problem statement & scope
│   ├── context.txt                 # Problem statement (plain text)
│   ├── architecture.md             # This document
│   └── implementation-plan.md      # Phase-wise implementation plan
│
├── backend/                        # Python — deployed to Railway
│   ├── src/
│   │   ├── ingestion/
│   │   │   ├── __init__.py
│   │   │   ├── base_scraper.py        # Abstract scraper interface
│   │   │   ├── reddit_scraper.py      # Reddit via Apify
│   │   │   ├── quora_scraper.py       # Quora via Apify
│   │   │   ├── appstore_scraper.py    # App Store reviews
│   │   │   ├── playstore_scraper.py   # Play Store reviews
│   │   │   ├── youtube_scraper.py     # YouTube comments via Apify + Data API v3
│   │   │   ├── instagram_scraper.py   # Instagram comments & threads via Apify
│   │   │   ├── myntra_scraper.py      # Myntra product reviews
│   │   │   ├── forum_scraper.py       # Fashion forums (HTTP + BS4)
│   │   │   ├── research_ingester.py   # User interviews & surveys (file-based)
│   │   │   └── config.py              # Query terms, rate limits, recency window
│   │   │
│   │   ├── cleaning/
│   │   │   ├── __init__.py
│   │   │   ├── pii_stripper.py        # Regex + spaCy NER PII removal
│   │   │   ├── deduplicator.py        # MinHash near-duplicate detection
│   │   │   ├── spam_filter.py         # Boilerplate & spam removal
│   │   │   ├── relevance_filter.py    # Keyword + LLM relevance classifier
│   │   │   └── chunker.py             # Long-form → analyzable units
│   │   │
│   │   ├── analysis/
│   │   │   ├── __init__.py
│   │   │   ├── theme_extractor.py     # Pass 1: micro-theme extraction
│   │   │   ├── theme_consolidator.py  # Pass 2: merge into macro-themes
│   │   │   ├── research_mapper.py     # Map themes → RQ1–RQ10
│   │   │   └── prompts.py             # All LLM prompt templates
│   │   │
│   │   ├── quantification/
│   │   │   ├── __init__.py
│   │   │   ├── scorer.py              # Frequency, spread, relevance scoring
│   │   │   ├── segment_slicer.py      # Category, price, occasion segmentation
│   │   │   └── matrix_generator.py    # Opportunity matrix output
│   │   │
│   │   ├── rag/
│   │   │   ├── __init__.py
│   │   │   ├── rag_config.py          # Configurable retrieval/embedding settings
│   │   │   ├── embedder.py            # BGE-small embedding (bge-small-en-v1.5)
│   │   │   ├── reranker.py            # Cross-encoder reranker
│   │   │   ├── vector_store.py        # ChromaDB / FAISS wrapper
│   │   │   ├── retriever.py           # Retrieve → rerank → top-K pipeline
│   │   │   ├── generator.py           # LLM answer generation with citation validation
│   │   │   └── evaluator.py           # Retrieval benchmark (Recall@K, MRR)
│   │   │
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── config.py              # Centralized config & env loader
│   │       ├── cache.py               # Intermediate result caching
│   │       ├── rate_limiter.py        # Per-platform rate limiting
│   │       ├── llm_client.py          # Unified LLM interface (Gemini/Ollama)
│   │       └── logger.py              # Structured logging
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI app entry point
│   │   ├── routes/
│   │   │   ├── query.py               # POST /api/query — RAG Q&A
│   │   │   ├── themes.py              # GET /api/themes — theme data
│   │   │   ├── matrix.py              # GET /api/matrix — opportunity matrix
│   │   │   └── report.py              # GET /api/report — full report
│   │   └── middleware/
│   │       └── cors.py                # CORS config for Vercel frontend
│   │
│   ├── data/
│   │   ├── raw/                       # Raw JSONL per platform per run
│   │   ├── clean/                     # Cleaned corpus (corpus.jsonl)
│   │   ├── themes/                    # Theme registry (themes.jsonl)
│   │   ├── matrix/                    # Opportunity matrix (matrix.json)
│   │   ├── research/                  # First-party research data
│   │   │   ├── interviews/            # Interview transcripts (anonymized)
│   │   │   └── surveys/               # Survey response exports
│   │   └── vectorstore/               # ChromaDB / FAISS index files
│   │
│   ├── reports/
│   │   ├── opportunity_report.md      # Thematic opportunity report
│   │   ├── segment_view.md            # Segment-cut breakdowns
│   │   └── privacy_log.md             # Data exclusion & anonymization log
│   │
│   ├── pipeline.py                    # Main orchestrator — runs all stages
│   ├── requirements.txt               # Python dependencies
│   ├── Procfile                       # Railway entry point
│   ├── railway.toml                   # Railway config
│   └── Makefile                       # Convenience targets
│
├── frontend/                          # Next.js — deployed to Vercel
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx               # Landing / chat page
│   │   │   ├── report/page.tsx        # Opportunity report viewer
│   │   │   ├── matrix/page.tsx        # Opportunity matrix visualization
│   │   │   └── layout.tsx             # Root layout
│   │   ├── components/
│   │   │   ├── ChatInterface.tsx       # RAG Q&A chat component
│   │   │   ├── CitationCard.tsx        # Source citation display
│   │   │   ├── ThemeCard.tsx           # Theme summary card
│   │   │   └── MatrixChart.tsx         # Opportunity matrix chart
│   │   └── lib/
│   │       └── api.ts                 # Backend API client
│   ├── package.json
│   ├── next.config.js
│   ├── vercel.json                    # Vercel config
│   └── tsconfig.json
│
└── README.md                          # Setup, usage, architecture overview
```

---

## 6. Data Flow — End to End

```mermaid
sequenceDiagram
    participant User as PM / Stakeholder
    participant Pipeline as pipeline.py
    participant Ingest as Ingestion Layer
    participant Clean as Cleaning Layer
    participant Analyze as Analysis Engine
    participant Quant as Quantification
    participant RAG as RAG Assistant
    participant LLM as LLM (Gemini / Ollama)
    participant Disk as Local Disk

    User->>Pipeline: Run pipeline (make all)
    
    Pipeline->>Ingest: fetch_all_sources()
    Ingest->>Disk: Write raw/*.jsonl
    Note over Ingest: ~5K–20K raw records

    Pipeline->>Clean: clean_corpus()
    Clean->>Disk: Read raw/*.jsonl
    Clean->>Disk: Write clean/corpus.jsonl
    Clean->>Disk: Write reports/privacy_log.md
    Note over Clean: ~3K–12K clean chunks

    Pipeline->>Analyze: extract_themes()
    Analyze->>Disk: Read clean/corpus.jsonl
    Analyze->>LLM: Pass 1 — micro-theme extraction (batched)
    LLM-->>Analyze: Micro-themes
    Analyze->>LLM: Pass 2 — theme consolidation
    LLM-->>Analyze: 10–25 macro-themes
    Analyze->>Disk: Write themes/themes.jsonl

    Pipeline->>Quant: score_and_rank()
    Quant->>Disk: Read themes/themes.jsonl
    Quant->>LLM: Purchase-delay relevance scoring
    LLM-->>Quant: Scores
    Quant->>Disk: Write matrix/matrix.json
    Quant->>Disk: Write reports/opportunity_report.md
    Quant->>Disk: Write reports/segment_view.md

    Pipeline->>RAG: build_index()
    RAG->>Disk: Read clean/corpus.jsonl + themes/themes.jsonl
    RAG->>Disk: Write vectorstore/ (ChromaDB)

    User->>RAG: "Why do users abandon wishlisted items?"
    RAG->>RAG: Embed query
    RAG->>Disk: Top-K retrieval from vectorstore
    RAG->>LLM: Generate cited answer
    LLM-->>RAG: Answer with citations
    RAG-->>User: Cited response
```

---

## 7. LLM Usage & Token Budget

### 7.1 Token Estimation

| Stage | Calls | Input Tokens/Call | Output Tokens/Call | Total Tokens |
|---|---|---|---|---|
| **Theme Extraction (Pass 1)** | ~250 batches (5K chunks ÷ 20) | ~6,000 | ~1,500 | ~1,875,000 |
| **Theme Consolidation (Pass 2)** | 1–3 calls | ~8,000 | ~3,000 | ~33,000 |
| **Purchase-Delay Scoring** | 1 call (all themes) | ~4,000 | ~1,000 | ~5,000 |
| **RAG Generation** | ~50 queries (interactive) | ~3,000 | ~500 | ~175,000 |
| **Total** | | | | **~2.1M tokens** |

### 7.2 Free-Tier Fit

| Provider | Free Tier Limit | Fits? |
|---|---|---|
| **Google Gemini (1.5 Flash)** | 1M tokens/minute, 1,500 req/day | ✅ Spread across multiple days |
| **Google Gemini (2.0 Flash)** | Similar generous free tier | ✅ |
| **Ollama (local)** | Unlimited (local compute) | ✅ Fallback option |

### 7.3 Cost Mitigation

- **Caching:** Every LLM response is cached to `data/themes/.cache/`. Re-runs skip already-processed batches.
- **Compression:** Chunks are pre-summarized where > 500 tokens before theme extraction.
- **Batching:** 20 chunks per call minimizes overhead.
- **Fallback:** If free-tier quota is exhausted, switch to Ollama with a local model (e.g., Llama 3, Mistral).

---

## 8. Privacy & Compliance Architecture

```mermaid
flowchart LR
    Raw["Raw Data\n(transient)"] -->|PII Strip| Clean["Clean Corpus\n(PII-free)"]
    Clean --> Themes["Theme Registry\n(PII-free)"]
    Clean --> VStore["Vector Store\n(PII-free)"]
    Themes --> Report["Reports\n(PII-free)"]
    VStore --> RAGResp["RAG Responses\n(PII-free)"]

    Raw -.->|"Logged: counts of\nstripped fields"| PrivLog["Privacy Log"]

    style Raw fill:#5c1a1a,stroke:#d94a4a,color:#fff
    style Clean fill:#1a4a1a,stroke:#4ad94a,color:#fff
    style PrivLog fill:#4a4a1a,stroke:#d9d94a,color:#fff
```

| Checkpoint | What Happens |
|---|---|
| **Ingestion** | Raw schema has no PII fields by design. URLs retained for traceability, but no author/user info. |
| **Cleaning — PII Stripper** | Regex catches `@handles`, emails, phone numbers. spaCy NER catches names. All removals logged by count and type. |
| **Theme Evidence** | Verbatim snippets are reviewed; any surviving PII is caught by a final regex pass before report generation. |
| **RAG Responses** | System prompt instructs LLM to never reproduce identifying information. Retrieved chunks are already PII-free. |
| **Privacy Log** | Auto-generated at each pipeline run: counts of stripped fields, filtered records, and rationale. |

---

## 9. Research Question Coverage Map

Every theme is tagged with the research questions it addresses. The final report ensures complete coverage:

| ID | Research Question | Expected Theme Sources |
|---|---|---|
| RQ1 | Why do users add products to wishlist? | Intent signals, bookmarking behavior |
| RQ2 | What prevents wishlisted items from being purchased? | Purchase blockers, friction themes |
| RQ3 | What uncertainties remain after liking a product? | Fit/size doubts, quality concerns |
| RQ4 | What causes users to postpone purchase? | Price waiting, occasion timing |
| RQ5 | How do users compare shortlisted products? | Comparison behavior, cross-platform research |
| RQ6 | What info do users seek outside Myntra/AJIO? | External research, YouTube reviews, social proof |
| RQ7 | Role of fit, size, styling, price, reviews, occasion, social validation? | Multi-factor decision themes |
| RQ8 | Wishlist as intent vs. bookmarking? | Behavioral segmentation themes |
| RQ9 | How do behaviors differ across segments? | Segment-cut analysis |
| RQ10 | What unmet needs connect to 30-day conversion? | Gap themes, conversion-linked frictions |

---

## 10. Operational Runbook

### 10.1 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# 2. Run full pipeline
python pipeline.py --all

# 3. Or run stages individually
python pipeline.py --ingest      # Stage 1
python pipeline.py --clean       # Stage 2
python pipeline.py --analyze     # Stage 3
python pipeline.py --quantify    # Stage 4
python pipeline.py --rag-build   # Stage 5 (build index)

# 4. Launch RAG assistant
python pipeline.py --rag-serve   # Interactive Q&A
```

### 10.2 Makefile Targets

```makefile
ingest:    python pipeline.py --ingest
clean:     python pipeline.py --clean
analyze:   python pipeline.py --analyze
quantify:  python pipeline.py --quantify
rag-build: python pipeline.py --rag-build
rag-serve: python pipeline.py --rag-serve
all:       python pipeline.py --all
report:    python pipeline.py --quantify  # regenerates reports
```

### 10.3 Re-Run Behavior

| Scenario | Behavior |
|---|---|
| Re-run ingestion | Fetches new data; appends to existing raw files (dedup catches overlaps downstream) |
| Re-run cleaning | Reprocesses all raw files; overwrites `corpus.jsonl` |
| Re-run analysis | Skips cached batches; only processes new/changed chunks |
| Re-run quantification | Recalculates scores from current theme registry |
| Re-run RAG build | Rebuilds vector index from current corpus + themes |

---

## 11. Known Limitations & Mitigations

| Limitation | Impact | Mitigation |
|---|---|---|
| Free-tier API quotas | May throttle ingestion or LLM calls | Spread runs across days; use Ollama as fallback |
| Theme quality depends on LLM | Themes may be too broad or too narrow | Human review step; tune consolidation prompt |
| Segment inference is text-based | Cannot segment by actual user demographics | Clearly label as "inferred from text mentions" |
| No real-time data | Corpus is a snapshot, not a live feed | Document recency window; re-run quarterly |
| Hindi/Hinglish content | spaCy NER less reliable for Hinglish | Retain but flag Hinglish chunks; manual review |
| Small forums may have thin data | Low volume may not reach thematic saturation | Prioritize Reddit/App Store; note coverage gaps |

---

## 12. Relationship to Downstream Work

```mermaid
flowchart LR
    Engine["Discovery Engine\n(THIS SYSTEM)"] -->|"Opportunity Report\n+ RAG Access"| Solution["Solution Design\n(OUT OF SCOPE)"]
    Solution -->|"Non-monetary\nintervention"| Implementation["Implementation\n(OUT OF SCOPE)"]

    style Engine fill:#1e3a5f,stroke:#4a90d9,color:#fff
    style Solution fill:#333,stroke:#666,color:#999
    style Implementation fill:#333,stroke:#666,color:#999
```

This architecture covers the **Discovery Engine only**. The eventual non-monetary solution design consumes this engine's output (opportunity report + RAG assistant) as input — it is a separate, later deliverable.
