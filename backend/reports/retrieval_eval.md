# Phase 5.8b: Retrieval Evaluation Benchmark Report

**Generated:** 2026-09-02 18:35:45  
**Total Benchmark Queries:** 25  
**Embedding Model:** `BAAI/bge-small-en-v1.5` (384-dim)  
**Cross-Encoder Reranker:** `cross-encoder/ms-marco-MiniLM-L-6-v2`  
**Vector Store:** ChromaDB Persistent (`data/chroma`)  

---

## 1. Executive Summary & Quality Gates

| Metric | Target | BGE-Only (Dense) | BGE + Cross-Encoder | Lift | Status |
|---|:---:|:---:|:---:|:---:|:---:|
| **Recall@5** | $\ge 0.70$ | `0.390` | **`1.000`** | **`+156.4%`** | ✅ PASS |
| **Recall@10** | $\ge 0.85$ | `0.448` | **`1.000`** | — | ✅ PASS |
| **MRR** | $\ge 0.60$ | `0.727` | **`1.000`** | **`+37.6%`** | ✅ PASS |
| **Reranker Lift** | $\ge +10\%$ | — | — | **`+156.4%`** | ✅ PASS |

---

## 2. Breakdown by Language

The benchmark tests retrieval across English (`en`), pure Hindi (`hi`), and Romanized conversational Hinglish (`hinglish`):

| Language | Query Count | Recall@5 | Recall@10 | MRR | Target Met |
|---|:---:|:---:|:---:|:---:|:---:|
| **English (en)** | 14 | `1.000` | `1.000` | `1.000` | ✅ PASS |
| **Hindi (hi)** | 2 | `1.000` | `1.000` | `1.000` | ✅ PASS |
| **Hinglish** | 9 | `1.000` | `1.000` | `1.000` | ✅ PASS |

---

## 3. Detailed Per-Query Results

| ID | Query Text | Lang | RQ | Recall@5 (Dense) | Recall@5 (Reranked) | MRR |
|---|---|:---:|:---:|:---:|:---:|:---:|
| **BQ-01** | Why do users add items to their wishlist? | `en` | `RQ1` | `0.50` | **`1.00`** | `1.00` |
| **BQ-02** | What prevents users from buying wishlisted items? | `en` | `RQ2` | `0.25` | **`1.00`** | `1.00` |
| **BQ-03** | How do size and fit concerns affect fashion purchases? | `en` | `RQ3, RQ7` | `0.25` | **`1.00`** | `1.00` |
| **BQ-04** | Do users use the wishlist as a bookmarking tool? | `en` | `RQ8` | `0.50` | **`1.00`** | `1.00` |
| **BQ-05** | What do users search for outside Myntra before buying? | `en` | `RQ6` | `0.25` | **`1.00`** | `1.00` |
| **BQ-06** | myntra pe wishlist mein kyun rakhte ho? | `hi` | `RQ1` | `0.25` | **`1.00`** | `1.00` |
| **BQ-07** | why myntra ki wishlist se kuch nahi khareedta | `hinglish` | `RQ2` | `0.25` | **`1.00`** | `1.00` |
| **BQ-08** | What causes users to postpone a purchase? | `en` | `RQ4` | `0.25` | **`1.00`** | `1.00` |
| **BQ-09** | How do users compare multiple shortlisted products? | `en` | `RQ5` | `0.50` | **`1.00`** | `1.00` |
| **BQ-10** | What role do customer reviews and unedited daylight photos play? | `en` | `RQ7` | `0.25` | **`1.00`** | `1.00` |
| **BQ-11** | How do wishlist behaviors differ across user segments? | `en` | `RQ9` | `0.00` | **`1.00`** | `1.00` |
| **BQ-12** | What unmet needs emerge consistently across user conversations? | `en` | `RQ10` | `0.75` | **`1.00`** | `1.00` |
| **BQ-13** | price drop ka wait karte hain sale ke liye | `hinglish` | `RQ4` | `0.50` | **`1.00`** | `1.00` |
| **BQ-14** | kapdo ka size kaisa hoga return karne ka dar | `hi` | `RQ3, RQ7` | `0.25` | **`1.00`** | `1.00` |
| **BQ-15** | friends se whatsapp pe screenshot share karke poochte hain | `hinglish` | `RQ7` | `0.00` | **`1.00`** | `1.00` |
| **BQ-16** | ajio ya nykaa pe sasta milta hai kya coupon code | `hinglish` | `RQ5, RQ6` | `0.25` | **`1.00`** | `1.00` |
| **BQ-17** | wishlist bohot clutter ho gayi hai 1000 items limit reached | `hinglish` | `RQ10` | `0.50` | **`1.00`** | `1.00` |
| **BQ-18** | wedding aur vacation ke liye dresses save kiye hain | `hinglish` | `RQ3` | `1.00` | **`1.00`** | `1.00` |
| **BQ-19** | real daylight photos chahiye studio lighting pe trust nahi hai | `hinglish` | `RQ7` | `1.00` | **`1.00`** | `1.00` |
| **BQ-20** | side by side comparison tool hona chahiye fabric check karne ke liye | `hinglish` | `RQ10` | `0.25` | **`1.00`** | `1.00` |
| **BQ-21** | Does the 1000 item limit cause decision paralysis? | `en` | `RQ10` | `0.75` | **`1.00`** | `1.00` |
| **BQ-22** | Why do shoppers abandon their wishlist during checkout? | `en` | `RQ2` | `0.50` | **`1.00`** | `1.00` |
| **BQ-23** | kya bargain hunters sirf EORS sale ka wait karte hain? | `hinglish` | `RQ9` | `0.50` | **`1.00`** | `1.00` |
| **BQ-24** | Is sizing inconsistency between brands causing checkout hesitation? | `en` | `RQ3` | `0.25` | **`1.00`** | `1.00` |
| **BQ-25** | Cross-app coupon comparison between Myntra and competitors | `en` | `RQ6` | `0.00` | **`1.00`** | `1.00` |

---
*Report generated automatically by Phase 5.8b RetrievalEvaluator.*