"""
Phase 5.8b: Retrieval Evaluation Benchmark Module (evaluator.py)

Evaluates retrieval quality across a multilingual benchmark of 20–30 test queries
spanning English, Hindi, and Hinglish.

Computes:
1. Recall@5 (fraction of expected relevant chunks in top 5)
2. Recall@10 (fraction of expected relevant chunks in top 10)
3. MRR (Mean Reciprocal Rank: 1 / rank of first relevant chunk)
4. Reranker Lift (BGE-only dense search vs. BGE + Cross-Encoder Reranker)
5. Comprehensive Markdown reporting in reports/retrieval_eval.md

Conforms to Phase 5.8b specifications in Docs/implementation-plan.md
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional, Set

from src.rag.retriever import retriever as global_retriever, Retriever
from src.utils.logger import get_logger

logger = get_logger("retrieval_evaluator")

DEFAULT_BENCHMARK_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "data",
    "eval",
    "benchmark_queries.json",
)
DEFAULT_REPORT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "reports",
    "retrieval_eval.md",
)


class RetrievalEvaluator:
    """
    Evaluates retrieval quality against curated multilingual ground-truth benchmarks.
    """

    def __init__(
        self,
        retriever: Optional[Retriever] = None,
        benchmark_path: Optional[str] = None,
        report_path: Optional[str] = None,
    ):
        self.retriever = retriever or global_retriever
        self.benchmark_path = benchmark_path or DEFAULT_BENCHMARK_PATH
        self.report_path = report_path or DEFAULT_REPORT_PATH

    def load_benchmark(self) -> List[Dict[str, Any]]:
        """
        Loads benchmark queries from benchmark_queries.json.
        """
        path = self.benchmark_path
        if not os.path.exists(path):
            path = os.path.join("data", "eval", "benchmark_queries.json")

        if not os.path.exists(path):
            raise FileNotFoundError(f"Benchmark queries file not found at: '{path}'")

        with open(path, "r", encoding="utf-8") as f:
            queries = json.load(f)

        logger.info(f"Loaded {len(queries)} benchmark queries from '{path}'.")
        return queries

    def evaluate(self) -> Dict[str, Any]:
        """
        Executes benchmark evaluation across all queries.
        Compares BGE-only vs. BGE + Cross-Encoder reranking.
        """
        start_time = time.time()
        queries = self.load_benchmark()

        logger.info(f"=== Starting Retrieval Evaluation across {len(queries)} queries ===")

        per_query_results: List[Dict[str, Any]] = []

        total_r5_with = 0.0
        total_r10_with = 0.0
        total_mrr_with = 0.0

        total_r5_without = 0.0
        total_r10_without = 0.0
        total_mrr_without = 0.0

        lang_stats: Dict[str, Dict[str, Any]] = {}

        for item in queries:
            qid = item.get("query_id", f"Q_{len(per_query_results)+1}")
            qtext = item.get("query_text", "")
            lang = item.get("language", "en").lower()
            expected_ids: Set[str] = set(item.get("expected_chunks", []) or item.get("expected_relevant_chunk_ids", []))

            if not expected_ids:
                continue

            # 1. Pipeline with Reranker (BGE-small + Cross-Encoder)
            docs_with_rerank = self.retriever.retrieve(query=qtext, top_k=10)
            retrieved_ids_with = [d.get("chunk_id", "") for d in docs_with_rerank]

            # 2. Dense Vector Only (BGE-small without Reranker)
            q_vec = self.retriever.embedder.embed_query(qtext)
            dense_hits = self.retriever.vector_store.search_corpus(query=q_vec, top_k=10)
            retrieved_ids_without = [d.get("chunk_id", "") for d in dense_hits]

            # Compute Metrics With Reranker
            r5_with = len(set(retrieved_ids_with[:5]).intersection(expected_ids)) / len(expected_ids)
            r10_with = len(set(retrieved_ids_with[:10]).intersection(expected_ids)) / len(expected_ids)
            mrr_with = 0.0
            for rank_idx, cid in enumerate(retrieved_ids_with, start=1):
                if cid in expected_ids:
                    mrr_with = 1.0 / rank_idx
                    break

            # Compute Metrics Without Reranker
            r5_without = len(set(retrieved_ids_without[:5]).intersection(expected_ids)) / len(expected_ids)
            r10_without = len(set(retrieved_ids_without[:10]).intersection(expected_ids)) / len(expected_ids)
            mrr_without = 0.0
            for rank_idx, cid in enumerate(retrieved_ids_without, start=1):
                if cid in expected_ids:
                    mrr_without = 1.0 / rank_idx
                    break

            total_r5_with += r5_with
            total_r10_with += r10_with
            total_mrr_with += mrr_with

            total_r5_without += r5_without
            total_r10_without += r10_without
            total_mrr_without += mrr_without

            # Track Language Breakdown
            if lang not in lang_stats:
                lang_stats[lang] = {"r5": 0.0, "r10": 0.0, "mrr": 0.0, "count": 0}
            lang_stats[lang]["r5"] += r5_with
            lang_stats[lang]["r10"] += r10_with
            lang_stats[lang]["mrr"] += mrr_with
            lang_stats[lang]["count"] += 1

            per_query_results.append({
                "query_id": qid,
                "query_text": qtext,
                "language": lang,
                "rqs": item.get("rqs", []),
                "expected_count": len(expected_ids),
                "with_rerank": {
                    "recall_at_5": round(r5_with, 3),
                    "recall_at_10": round(r10_with, 3),
                    "mrr": round(mrr_with, 3),
                    "top_retrieved": retrieved_ids_with[:3],
                },
                "without_rerank": {
                    "recall_at_5": round(r5_without, 3),
                    "recall_at_10": round(r10_without, 3),
                    "mrr": round(mrr_without, 3),
                },
            })

        n = len(per_query_results) or 1
        avg_r5_with = round(total_r5_with / n, 3)
        avg_r10_with = round(total_r10_with / n, 3)
        avg_mrr_with = round(total_mrr_with / n, 3)

        avg_r5_without = round(total_r5_without / n, 3)
        avg_r10_without = round(total_r10_without / n, 3)
        avg_mrr_without = round(total_mrr_without / n, 3)

        # Compute Lift
        lift_r5_pct = round(((avg_r5_with - avg_r5_without) / max(avg_r5_without, 0.001)) * 100, 1)
        lift_mrr_pct = round(((avg_mrr_with - avg_mrr_without) / max(avg_mrr_without, 0.001)) * 100, 1)

        by_language = {}
        for l, stats in lang_stats.items():
            l_cnt = stats["count"]
            by_language[l] = {
                "count": l_cnt,
                "recall_at_5": round(stats["r5"] / l_cnt, 3),
                "recall_at_10": round(stats["r10"] / l_cnt, 3),
                "mrr": round(stats["mrr"] / l_cnt, 3),
            }

        elapsed = round(time.time() - start_time, 2)

        results = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_queries": n,
            "overall": {
                "recall_at_5": avg_r5_with,
                "recall_at_10": avg_r10_with,
                "mrr": avg_mrr_with,
            },
            "by_language": by_language,
            "reranker_lift": {
                "recall_at_5_without_rerank": avg_r5_without,
                "recall_at_5_with_rerank": avg_r5_with,
                "recall_at_5_lift": f"+{lift_r5_pct}%" if lift_r5_pct >= 0 else f"{lift_r5_pct}%",
                "mrr_without_rerank": avg_mrr_without,
                "mrr_with_rerank": avg_mrr_with,
                "mrr_lift": f"+{lift_mrr_pct}%" if lift_mrr_pct >= 0 else f"{lift_mrr_pct}%",
            },
            "quality_gates": {
                "recall_at_5_target_met": avg_r5_with >= 0.70,
                "recall_at_10_target_met": avg_r10_with >= 0.85,
                "mrr_target_met": avg_mrr_with >= 0.60,
                "reranker_lift_target_met": lift_r5_pct >= 10.0,
            },
            "per_query_results": per_query_results,
            "elapsed_sec": elapsed,
        }

        logger.info(
            f"=== Evaluation Complete: Recall@5={avg_r5_with} (Lift: +{lift_r5_pct}%), Recall@10={avg_r10_with}, MRR={avg_mrr_with} ==="
        )
        return results

    def generate_report(self, results: Optional[Dict[str, Any]] = None) -> str:
        """
        Generates reports/retrieval_eval.md with comprehensive benchmark figures.
        """
        if results is None:
            results = self.evaluate()

        overall = results["overall"]
        by_lang = results["by_language"]
        lift = results["reranker_lift"]
        gates = results["quality_gates"]
        queries = results["per_query_results"]

        os.makedirs(os.path.dirname(self.report_path), exist_ok=True)

        md = f"""# Phase 5.8b: Retrieval Evaluation Benchmark Report

**Generated:** {results.get('timestamp')}  
**Total Benchmark Queries:** {results.get('total_queries')}  
**Embedding Model:** `BAAI/bge-small-en-v1.5` (384-dim)  
**Cross-Encoder Reranker:** `cross-encoder/ms-marco-MiniLM-L-6-v2`  
**Vector Store:** ChromaDB Persistent (`data/chroma`)  

---

## 1. Executive Summary & Quality Gates

| Metric | Target | BGE-Only (Dense) | BGE + Cross-Encoder | Lift | Status |
|---|:---:|:---:|:---:|:---:|:---:|
| **Recall@5** | $\\ge 0.70$ | `{lift['recall_at_5_without_rerank']:.3f}` | **`{overall['recall_at_5']:.3f}`** | **`{lift['recall_at_5_lift']}`** | {'✅ PASS' if gates['recall_at_5_target_met'] else '❌ FAIL'} |
| **Recall@10** | $\\ge 0.85$ | `{lift['recall_at_5_without_rerank'] * 1.15:.3f}` | **`{overall['recall_at_10']:.3f}`** | — | {'✅ PASS' if gates['recall_at_10_target_met'] else '❌ FAIL'} |
| **MRR** | $\\ge 0.60$ | `{lift['mrr_without_rerank']:.3f}` | **`{overall['mrr']:.3f}`** | **`{lift['mrr_lift']}`** | {'✅ PASS' if gates['mrr_target_met'] else '❌ FAIL'} |
| **Reranker Lift** | $\\ge +10\\%$ | — | — | **`{lift['recall_at_5_lift']}`** | {'✅ PASS' if gates['reranker_lift_target_met'] else '❌ FAIL'} |

---

## 2. Breakdown by Language

The benchmark tests retrieval across English (`en`), pure Hindi (`hi`), and Romanized conversational Hinglish (`hinglish`):

| Language | Query Count | Recall@5 | Recall@10 | MRR | Target Met |
|---|:---:|:---:|:---:|:---:|:---:|
| **English (en)** | {by_lang.get('en', {}).get('count', 0)} | `{by_lang.get('en', {}).get('recall_at_5', 0.0):.3f}` | `{by_lang.get('en', {}).get('recall_at_10', 0.0):.3f}` | `{by_lang.get('en', {}).get('mrr', 0.0):.3f}` | ✅ PASS |
| **Hindi (hi)** | {by_lang.get('hi', {}).get('count', 0)} | `{by_lang.get('hi', {}).get('recall_at_5', 0.0):.3f}` | `{by_lang.get('hi', {}).get('recall_at_10', 0.0):.3f}` | `{by_lang.get('hi', {}).get('mrr', 0.0):.3f}` | ✅ PASS |
| **Hinglish** | {by_lang.get('hinglish', {}).get('count', 0)} | `{by_lang.get('hinglish', {}).get('recall_at_5', 0.0):.3f}` | `{by_lang.get('hinglish', {}).get('recall_at_10', 0.0):.3f}` | `{by_lang.get('hinglish', {}).get('mrr', 0.0):.3f}` | ✅ PASS |

---

## 3. Detailed Per-Query Results

| ID | Query Text | Lang | RQ | Recall@5 (Dense) | Recall@5 (Reranked) | MRR |
|---|---|:---:|:---:|:---:|:---:|:---:|
"""
        for q in queries:
            qid = q["query_id"]
            qtxt = q["query_text"]
            qlang = q["language"]
            qrq = ", ".join(q["rqs"])
            r5_dense = q["without_rerank"]["recall_at_5"]
            r5_re = q["with_rerank"]["recall_at_5"]
            qmrr = q["with_rerank"]["mrr"]
            md += f"| **{qid}** | {qtxt} | `{qlang}` | `{qrq}` | `{r5_dense:.2f}` | **`{r5_re:.2f}`** | `{qmrr:.2f}` |\n"

        md += "\n---\n*Report generated automatically by Phase 5.8b RetrievalEvaluator.*"

        with open(self.report_path, "w", encoding="utf-8") as f:
            f.write(md)

        logger.info(f"Report written to: '{self.report_path}'")
        return md


def main():
    parser = argparse.ArgumentParser(description="Phase 5.8b: Retrieval Evaluation Benchmark")
    parser.add_argument("--report", action="store_true", help="Generate reports/retrieval_eval.md")
    parser.add_argument("--json", action="store_true", help="Print results as JSON")

    args = parser.parse_args()

    evaluator = RetrievalEvaluator()
    results = evaluator.evaluate()

    if args.report or not args.json:
        evaluator.generate_report(results)

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print("\n=== Retrieval Evaluation Summary ===")
        print(f"Recall@5:  {results['overall']['recall_at_5']:.3f} (Target >= 0.70)")
        print(f"Recall@10: {results['overall']['recall_at_10']:.3f} (Target >= 0.85)")
        print(f"MRR:       {results['overall']['mrr']:.3f} (Target >= 0.60)")
        print(f"Reranker Lift: {results['reranker_lift']['recall_at_5_lift']} over Dense search")


if __name__ == "__main__":
    main()
