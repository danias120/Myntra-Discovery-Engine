"""
Phase 0.6 Smoke Test Suite

Runs end-to-end sanity and import verification across all Phase 0 deliverables.
"""

import sys
import time
from pathlib import Path

# Setup paths
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(BACKEND_DIR / "src"))

results = []

def run_test(name: str, fn):
    print(f"Running [{name}]...", end=" ", flush=True)
    try:
        t0 = time.time()
        fn()
        elapsed = time.time() - t0
        print(f"✅ PASS ({elapsed:.2f}s)")
        results.append((name, True, f"{elapsed:.2f}s"))
    except Exception as e:
        print(f"❌ FAIL: {e}")
        results.append((name, False, str(e)))

# Test 1: spaCy model
def test_spacy():
    import spacy
    nlp = spacy.load("en_core_web_sm")
    doc = nlp("Myntra fashion haul was great.")
    assert len(doc) > 0

# Test 2: Apify Client
def test_apify():
    from apify_client import ApifyClient
    client = ApifyClient("dummy_token")
    assert client is not None

# Test 3: Google GenAI SDK
def test_gemini():
    from google import genai
    assert genai is not None

# Test 4: ChromaDB
def test_chromadb():
    import chromadb
    client = chromadb.Client()
    coll = client.create_collection("smoke_test_coll")
    coll.add(ids=["1"], documents=["test document"])
    res = coll.query(query_texts=["test"], n_results=1)
    assert len(res["ids"][0]) == 1

# Test 5: BGE-small Embeddings
def test_bge_small():
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("BAAI/bge-small-en-v1.5")
    vec = model.encode("Represent this sentence for searching: fashion wishlist", normalize_embeddings=True)
    assert len(vec) == 384

# Test 6: Cross-Encoder Reranker
def test_reranker():
    from sentence_transformers import CrossEncoder
    model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
    scores = model.predict([("fashion shopping", "user wanted to buy a dress on Myntra")])
    assert len(scores) == 1

# Test 7: tiktoken
def test_tiktoken():
    import tiktoken
    enc = tiktoken.get_encoding("cl100k_base")
    tokens = enc.encode("Testing token estimation for Gemini budget.")
    assert len(tokens) > 0

# Test 8: Data & Ingestion libraries
def test_libraries():
    import pandas as pd
    import datasketch
    import googleapiclient
    import sse_starlette
    df = pd.DataFrame({"a": [1, 2]})
    assert len(df) == 2

# Test 9: Utility Modules
def test_utils():
    from src.utils.config import get_config_summary, RAW_DIR
    from src.utils.logger import get_logger
    from src.utils.cache import default_cache
    from src.utils.rate_limiter import get_limiter
    from src.utils.llm_client import llm_client

    logger = get_logger("smoke_test")
    summary = get_config_summary()
    assert summary["LLM_PROVIDER"] is not None
    assert RAW_DIR.exists()
    
    key = default_cache.generate_key("test")
    default_cache.set(key, {"test": 123})
    assert default_cache.get(key)["test"] == 123
    
    limiter = get_limiter("gemini")
    assert limiter.rpm == 15
    
    est = llm_client.estimate_tokens("Hello world")
    assert est > 0

# Test 10: FastAPI app & Health endpoint
def test_api():
    from fastapi.testclient import TestClient
    from api.main import app
    client = TestClient(app)
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] in ("ok", "healthy")


def main():
    print("=" * 60)
    print("  Discovery Engine — Phase 0.6 Smoke Test Suite")
    print("=" * 60)
    
    run_test("G0.4 spaCy en_core_web_sm", test_spacy)
    run_test("G0.5 ApifyClient Import", test_apify)
    run_test("G0.6 Google GenAI SDK", test_gemini)
    run_test("G0.7 ChromaDB In-Memory Store", test_chromadb)
    run_test("G0.8 BGE-small Model (384-dim)", test_bge_small)
    run_test("G0.9 CrossEncoder Reranker", test_reranker)
    run_test("G0.10 tiktoken Tokenizer", test_tiktoken)
    run_test("G0.2 Secondary Libraries", test_libraries)
    run_test("G0.14 Utils Package", test_utils)
    run_test("G0.12 FastAPI /api/health", test_api)

    print("=" * 60)
    passed = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    print(f"Summary: {passed}/{total} smoke tests passed.")
    if passed == total:
        print("🎉 ALL PHASE 0 SMOKE TESTS PASSED!")
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED.")
        sys.exit(1)

if __name__ == "__main__":
    main()
