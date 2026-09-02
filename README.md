# Myntra Wishlist Discovery Engine

> AI-powered wishlist-to-purchase behavior discovery engine for the Myntra Growth team.

## Overview

A five-stage, offline-first pipeline that converts scattered public conversations about fashion wishlisting into a ranked, evidence-backed opportunity map — answering 10 research questions with every claim traceable to real user snippets.

## Quick Start

```bash
# 1. Setup backend
cd backend
pip install -r requirements.txt
python -m spacy download en_core_web_sm
cp .env.example .env   # Fill in API keys

# 2. Run full pipeline
make all

# 3. Launch RAG assistant
make api-dev
```

## Architecture

See [Docs/architecture.md](Docs/architecture.md) for the full system design.

## Documentation

| Document | Purpose |
|---|---|
| [context.md](Docs/context.md) | Problem statement & research scope |
| [architecture.md](Docs/architecture.md) | System architecture & technical design |
| [implementation-plan.md](Docs/implementation-plan.md) | Phase-wise implementation plan |
| [edge-cases.md](Docs/edge-cases.md) | Corner scenarios & handling |
| [eval.md](Docs/eval.md) | Phase-wise evaluation criteria |

## Tech Stack

- **Backend:** Python 3.10+ / FastAPI (Railway)
- **Frontend:** TypeScript / Next.js (Vercel)
- **Embeddings:** BAAI/bge-small-en-v1.5 (384-dim, local)
- **Reranker:** cross-encoder/ms-marco-MiniLM-L-6-v2 (local)
- **LLM:** Google Gemini free tier / Ollama (local fallback)
- **Vector Store:** ChromaDB

## License

Private — Myntra Growth Team internal use.
