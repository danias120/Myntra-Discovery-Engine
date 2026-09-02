# Problem Statement: AI-Powered Discovery Engine for Wishlist-to-Purchase Research (Myntra Growth Case)

## Overview

As part of the Myntra Growth team's mandate to increase the percentage of users who purchase at least one item from their wishlist within 30 days of adding it, the first phase of work is not designing a solution — it is understanding why the gap exists in the first place. Millions of users treat the wishlist as either a genuine purchase-intent signal or a passive bookmarking habit, and today that distinction is invisible to the business.

Before any intervention can be proposed — and note, one that cannot rely on monetary incentives such as discounts, cashback, or coupons — the team needs an evidence base built from how real users talk about wishlisting, shortlisting, and abandoning fashion purchases, not just on Myntra, but across the broader online fashion-shopping conversation happening on app stores, forums, and social platforms.

This problem statement covers only the discovery layer: an AI-powered system that ingests, cleans, thematically analyzes, and quantifies public conversations at scale, and exposes the resulting corpus through a lightweight retrieval-augmented (RAG) assistant for ad hoc follow-up questions. Proposing the actual non-monetary solution is a separate, downstream exercise that consumes this engine's output — it is explicitly out of scope here.

## Objective

Design and build a lightweight, near-zero-cost AI discovery engine that:

1. Collects publicly available user conversations about fashion shopping, wishlisting, and purchase decisions from multiple platforms
2. Cleans and normalizes that raw text into an analyzable corpus
3. Uses an LLM to cluster the corpus into themes, going beyond sentiment/summary to identify and quantify distinct opportunity areas
4. Maps findings back to the research questions the business has posed
5. Surfaces everything through a minimal RAG-based Q&A assistant so a PM or stakeholder can interrogate the corpus directly, with every answer grounded in and cited back to source snippets

## Target Users / Consumers

- **You (the PM)**, as the immediate operator of the pipeline
- **Growth/Product stakeholders** who will read the opportunity report to decide what non-monetary intervention to prototype next
- **Anyone using the RAG assistant** to ask a follow-up question the static report doesn't cover

## Research Questions the Engine Must Be Able to Answer

The thematic output must give evidence-backed answers — not opinions — to:

1. Why do users add fashion products to their wishlist?
2. What prevents wishlisted products from eventually being purchased?
3. What uncertainties remain after a user has identified a product they like?
4. What causes users to postpone a purchase?
5. How do users compare multiple shortlisted products?
6. What information do users seek outside Myntra/AJIO before purchasing?
7. What role do fit, size, styling, price, reviews, occasion, and social validation play?
8. When is the wishlist genuine purchase intent vs. a bookmarking mechanism?
9. How do these behaviors differ across user segments?
10. What unmet needs emerge consistently across conversations, and how do they connect to the 30-day conversion metric?

## Scope of Work

### 1. Data Sourcing & Ingestion

- **Sources:** App Store reviews, Play Store reviews, Reddit threads/comments, Quora, fashion/shopping forums and communities, social conversations, YouTube comments (on relevant haul/review/try-on videos), product review & Q&A sections
- Pull only publicly accessible content — no login-gated scraping, no bypassing ToS or rate limits
- Target a recency window (e.g., last 6–12 months) with enough volume per source to support thematic saturation, not just a handful of anecdotes
- Store raw pulls with source, platform, and timestamp metadata only — no reviewer-identifying fields (see Constraints)

### 2. Cleaning & Normalization

- De-duplicate, strip boilerplate/spam, filter off-topic or non-relevant content
- Strip usernames, handles, emails, or any other identifying fields before text reaches storage or any report
- Chunk long-form content (Reddit threads, YouTube comment sections) into analyzable units

### 3. Thematic Analysis Engine

- Use an LLM to cluster cleaned snippets into themes that map back to the research questions above (themes should emerge from the data, not be forced into a fixed taxonomy)
- For each theme, capture: a description, representative verbatim snippets, source-platform mix, and approximate share of corpus
- Explicitly go beyond sentiment polarity — the output is "what is the friction and how big is it," not "positive vs. negative"

### 4. Opportunity Quantification & Prioritization

- Score each theme on frequency, platform spread (how many distinct sources corroborate it), and inferred relevance to purchase delay or abandonment
- Produce a ranked opportunity list/matrix so stakeholders can see which frictions are both common and consequential, not a flat list of themes
- Where volume allows, break out how themes vary by inferred segment (category, price band mentioned, occasion vs. everyday purchases, etc.)

### 5. Lightweight RAG Assistant

- A minimal chat interface (CLI or simple web UI) that lets a user ask free-form questions against the cleaned corpus and generated theme summaries
- Every answer must cite the source platform/snippet it drew from and must not extend beyond what the retrieved evidence supports
- Retrieval stays small and cheap: chunk-level embeddings or a lightweight local vector store, top-k retrieval only — no fine-tuning, no paid vector database

## Constraints

### Cost

- The system must run at zero infrastructure cost beyond LLM token usage. No paid scraping proxies, no paid APIs, no paid hosting or vector databases.
- The pipeline should be token-efficient: summarize/compress before repeated LLM calls, cache intermediate outputs, avoid re-processing the same raw text.

### Legal & Ethical Data Collection

- Public, ToS-respecting sources only — no login-walled scraping, no circumventing rate limits or robots.txt
- No PII (usernames, emails, device or account identifiers) may be collected, stored, or displayed anywhere in the pipeline or its outputs

### Analytical Rigor

- No hallucinated themes — every claim in the report must trace back to at least one real snippet
- Sentiment-only or generic "users like/dislike X" summaries are not sufficient; each opportunity area needs a frequency/impact signal

### Solution Boundary

- This engine produces discovery output only. It does not propose or evaluate the eventual non-monetary intervention — that is a separate, later deliverable that consumes this engine's opportunity report

## Deliverables

1. **README** — architecture overview (ingestion → cleaning → theming → quantification → RAG), sources covered, how to run the pipeline, known limitations
2. **Corpus & ingestion pipeline** — scripts/workflows that pull and clean data from each source, retaining source and timestamp metadata
3. **Thematic opportunity report** — themes mapped to the research questions, each with description, anonymized verbatim quotes, frequency/source-spread data, and a prioritized opportunity matrix
4. **Segment-cut view** — where data supports it, a breakdown of how top themes differ across user/product segments
5. **Lightweight RAG assistant** — a working Q&A interface over the corpus, with source-cited responses
6. **Data & privacy log** — a short note on what was excluded or anonymized, and why

## Success Criteria

1. The report answers all ten posed research questions with evidence, not assumption
2. Opportunity areas are ranked and quantified, not just listed
3. Every theme and every RAG answer is traceable to a real, anonymized source snippet
4. The entire build runs within free-tier tools and LLM token usage, with no paid infrastructure
5. No PII appears anywhere in stored data, reports, or RAG responses
6. The output is specific enough that a follow-on solution-design exercise (non-monetary, by constraint) could act on it directly

## Summary

The goal is not to summarize reviews or run sentiment analysis — it's to turn scattered, public conversations about fashion wishlisting into a ranked, evidence-backed map of why high-intent demand on Myntra stalls before checkout. This is delivered through a free-to-run pipeline and a lightweight assistant that lets anyone interrogate the evidence directly, with the eventual non-monetary solution left as a deliberately separate next step.
