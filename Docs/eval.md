# Evaluation Criteria: Phase-Wise Quality Gates

> **Source:** Derived from [implementation-plan.md](file:///Users/daniamacbook/Desktop/NL%20Myntra/Docs/implementation-plan.md)
> **Purpose:** Define pass/fail criteria, quantitative benchmarks, automated test scripts, and manual review checklists for every phase — ensuring no phase exits without verified quality.

---

## How to Use This Document

Each phase section contains:

| Section | Purpose |
|---|---|
| **Gate Criteria** | Hard pass/fail checks — all must pass to proceed |
| **Quality Metrics** | Quantitative benchmarks with target thresholds |
| **Automated Tests** | Shell commands and scripts to run |
| **Manual Review Checklist** | Human-judgment items that require visual inspection |
| **Health Dashboard** | Key numbers to log and track |
| **Failure Protocol** | What to do if a gate fails |

**Gate status key:** ✅ Pass · ❌ Fail · ⚠️ Warning (proceed with caution)

---

## Phase 0: Project Setup & Scaffolding

### Gate Criteria

| # | Criterion | Test | Pass Condition |
|---|---|---|---|
| G0.1 | Python environment ready | `python --version` | 3.10+ |
| G0.2 | Node.js environment ready | `node --version` | 18+ |
| G0.3 | All Python deps install cleanly | `pip install -r requirements.txt` | Exit code 0, no errors |
| G0.4 | spaCy model downloaded | `python -c "import spacy; spacy.load('en_core_web_sm')"` | No `OSError` |
| G0.5 | Apify client importable | `python -c "from apify_client import ApifyClient"` | No `ImportError` |
| G0.6 | Gemini SDK importable | `python -c "from google import genai"` | No `ImportError` |
| G0.7 | ChromaDB creates in-memory store | `python -c "import chromadb; chromadb.Client()"` | No error |
| G0.8 | BGE-small model loads | `python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-small-en-v1.5')"` | Model downloaded and loaded |
| G0.9 | Reranker model loads | `python -c "from sentence_transformers import CrossEncoder; CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')"` | Model downloaded and loaded |
| G0.10 | tiktoken importable | `python -c "import tiktoken"` | No `ImportError` |
| G0.11 | Frontend builds | `cd frontend && npm install && npm run dev` (kill after 10s) | Dev server starts on port 3000 |
| G0.12 | Backend starts | `cd backend && uvicorn api.main:app --port 8000` (kill after 5s) | Server starts on port 8000 |
| G0.13 | Directory structure exists | Check all expected directories | All dirs in architecture.md §5 exist |
| G0.14 | `.env.example` has all keys | Check for `APIFY_API_TOKEN`, `GEMINI_API_KEY`, `YOUTUBE_API_KEY`, `LLM_PROVIDER` | All present |
| G0.15 | LLM client returns a test response | `python -c "from src.utils.llm_client import ...; generate('Say hello')"` | Non-empty string returned |

### Automated Test Script

```bash
#!/bin/bash
# Phase 0 Eval — run from backend/ directory
set -e

echo "=== Phase 0 Evaluation ==="

echo "[G0.1] Python version..."
python --version 2>&1 | grep -q "3.1[0-9]" && echo "✅ PASS" || echo "❌ FAIL"

echo "[G0.2] Node version..."
node --version 2>&1 | grep -qE "v(1[8-9]|2[0-9])" && echo "✅ PASS" || echo "❌ FAIL"

echo "[G0.3] Python deps..."
pip install -r requirements.txt --quiet 2>/dev/null && echo "✅ PASS" || echo "❌ FAIL"

echo "[G0.4] spaCy model..."
python -c "import spacy; spacy.load('en_core_web_sm'); print('✅ PASS')" 2>/dev/null || echo "❌ FAIL"

echo "[G0.5] Apify client..."
python -c "from apify_client import ApifyClient; print('✅ PASS')" 2>/dev/null || echo "❌ FAIL"

echo "[G0.6] Gemini SDK..."
python -c "from google import genai; print('✅ PASS')" 2>/dev/null || echo "❌ FAIL"

echo "[G0.7] ChromaDB..."
python -c "import chromadb; chromadb.Client(); print('✅ PASS')" 2>/dev/null || echo "❌ FAIL"

echo "[G0.8] BGE-small model..."
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-small-en-v1.5'); print('✅ PASS')" 2>/dev/null || echo "❌ FAIL"

echo "[G0.9] Reranker model..."
python -c "from sentence_transformers import CrossEncoder; CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2'); print('✅ PASS')" 2>/dev/null || echo "❌ FAIL"

echo "[G0.10] tiktoken..."
python -c "import tiktoken; print('✅ PASS')" 2>/dev/null || echo "❌ FAIL"

echo "[G0.13] Directory structure..."
for dir in src/ingestion src/cleaning src/analysis src/quantification src/rag src/utils api api/routes data/raw data/clean data/themes data/matrix data/research/interviews data/research/surveys data/vectorstore reports; do
    [ -d "$dir" ] || { echo "❌ FAIL — missing $dir"; exit 1; }
done
echo "✅ PASS"

echo "[G0.14] .env.example..."
for key in APIFY_API_TOKEN GEMINI_API_KEY YOUTUBE_API_KEY LLM_PROVIDER; do
    grep -q "$key" .env.example || { echo "❌ FAIL — missing $key in .env.example"; exit 1; }
done
echo "✅ PASS"

echo "=== Phase 0 Complete ==="
```

### Failure Protocol

| Failure | Action |
|---|---|
| Any `ImportError` | Fix `requirements.txt`, re-install |
| Model download fails | Check network; HuggingFace may be blocked. Download manually and cache. |
| Frontend won't start | Check `node_modules` installed; run `npm install` |
| LLM client test fails | Verify `.env` has valid `GEMINI_API_KEY` or Ollama is running |

---

## Phase 1: Data Sourcing & Ingestion

### Gate Criteria

| # | Criterion | Test | Pass Condition |
|---|---|---|---|
| G1.1 | Raw JSONL files exist | `ls data/raw/*.jsonl` | ≥3 files (one per platform) |
| G1.2 | Total record count ≥ 1,000 | `wc -l data/raw/*.jsonl` | Sum ≥ 1,000 |
| G1.3 | ≥ 3 distinct platforms have data | Count unique platform prefixes in filenames | ≥ 3 |
| G1.4 | Myntra product reviews present | `ls data/raw/myntra_reviews_*.jsonl` | File exists and has > 0 lines |
| G1.5 | Schema compliance | Validate every record against raw schema | 100% pass rate |
| G1.6 | No PII fields in raw records | `grep -i "username\|author\|email" data/raw/*.jsonl` | Zero matches |
| G1.7 | Records within recency window | Spot-check 20 random timestamps | All within last 12 months |
| G1.8 | Ingestion log exists | `cat data/raw/ingestion_log.json` | Valid JSON with per-platform stats |

### Quality Metrics

| Metric | Target | ⚠️ Warning | ❌ Fail |
|---|---|---|---|
| **Total raw records** | ≥ 1,000 | 500–999 | < 500 |
| **Platforms with data** | ≥ 5 | 3–4 | < 3 |
| **Records per platform (avg)** | ≥ 100 | 50–99 | < 50 |
| **Schema validation pass rate** | 100% | 95–99% | < 95% |
| **Apify quota remaining** | > 10% | 5–10% | 0% (exhausted) |
| **YouTube API quota remaining** | > 20% | 10–20% | 0% (exhausted) |
| **Scraper error rate** | < 5% | 5–15% | > 15% |
| **Research data files loaded** | ≥ 1 (if available) | 0 (no files provided) | Ingester crashed |
| **Empty records (text = "")** | 0 | 1–10 | > 10 |

### Automated Test Script

```bash
#!/bin/bash
# Phase 1 Eval — run from backend/ directory
echo "=== Phase 1 Evaluation ==="

echo "[G1.1] Raw JSONL files..."
FILE_COUNT=$(ls data/raw/*.jsonl 2>/dev/null | wc -l)
[ "$FILE_COUNT" -ge 3 ] && echo "✅ PASS ($FILE_COUNT files)" || echo "❌ FAIL ($FILE_COUNT files)"

echo "[G1.2] Total record count..."
TOTAL=$(cat data/raw/*.jsonl 2>/dev/null | wc -l)
if [ "$TOTAL" -ge 1000 ]; then echo "✅ PASS ($TOTAL records)"
elif [ "$TOTAL" -ge 500 ]; then echo "⚠️ WARNING ($TOTAL records — below target)"
else echo "❌ FAIL ($TOTAL records)"; fi

echo "[G1.3] Platform diversity..."
PLATFORMS=$(ls data/raw/*.jsonl | sed 's/.*\///' | sed 's/_[0-9].*//;s/_20[0-9].*//' | sort -u | wc -l)
[ "$PLATFORMS" -ge 3 ] && echo "✅ PASS ($PLATFORMS platforms)" || echo "❌ FAIL ($PLATFORMS platforms)"

echo "[G1.4] Myntra reviews..."
[ -f data/raw/myntra_reviews_*.jsonl ] 2>/dev/null && echo "✅ PASS" || echo "❌ FAIL — no Myntra reviews"

echo "[G1.5] Schema compliance (sample check)..."
python -c "
import json, sys
errors = 0
required = ['record_id', 'source_platform', 'text', 'ingestion_timestamp', 'source_type']
for f in __import__('glob').glob('data/raw/*.jsonl'):
    for i, line in enumerate(open(f)):
        try:
            r = json.loads(line)
            for k in required:
                if k not in r:
                    errors += 1
                    break
        except json.JSONDecodeError:
            errors += 1
if errors == 0: print('✅ PASS')
else: print(f'❌ FAIL — {errors} records failed schema validation')
"

echo "[G1.6] PII field check..."
PII=$(grep -liE '"(username|author|email|user_id)"' data/raw/*.jsonl 2>/dev/null | wc -l)
[ "$PII" -eq 0 ] && echo "✅ PASS" || echo "❌ FAIL — PII fields found in $PII files"

echo "[G1.8] Ingestion log..."
[ -f data/raw/ingestion_log.json ] && echo "✅ PASS" || echo "❌ FAIL — no ingestion log"

echo ""
echo "--- Per-Platform Record Counts ---"
for f in data/raw/*.jsonl; do
    echo "  $(basename $f): $(wc -l < $f) records"
done

echo "=== Phase 1 Complete ==="
```

### Manual Review Checklist

- [ ] Open 5 random records from each platform — does the text look like real user content?
- [ ] Check that no author names or @handles appear in the `text` field
- [ ] Verify that Myntra reviews have `product_category` and `product_name` in metadata
- [ ] Verify that research data (interviews/surveys) has `source_type: "first_party_research"`
- [ ] Check ingestion_log.json for any platforms with abnormally high error counts

### Failure Protocol

| Failure | Action |
|---|---|
| < 500 total records | Rerun with broader query terms; try additional platforms |
| < 3 platforms | Check scraper logs; fix broken scrapers; run skipped platforms |
| PII fields found | Fix scraper to strip author fields before record creation |
| Schema validation < 95% | Fix the offending scraper's record creation logic |
| Myntra reviews missing | Check if Myntra blocked the scraper; switch to Apify actor |

---

## Phase 2: Cleaning & Normalization

### Gate Criteria

| # | Criterion | Test | Pass Condition |
|---|---|---|---|
| G2.1 | Clean corpus exists | `wc -l data/clean/corpus.jsonl` | File exists, > 0 lines |
| G2.2 | Chunk count ≥ 500 | `wc -l data/clean/corpus.jsonl` | ≥ 500 |
| G2.3 | Zero PII in clean corpus | Regex + NER scan | Zero matches |
| G2.4 | All chunks have required fields | Schema validation | 100% pass rate |
| G2.5 | No exact duplicates | Hash dedup check on clean output | 0 exact duplicates |
| G2.6 | Privacy log generated | `cat reports/privacy_log.md` | File exists, has counts |
| G2.7 | Retention rate is 30–80% | `clean_count / raw_count` | Between 0.30 and 0.80 |
| G2.8 | No platform was entirely filtered out | Per-platform chunk counts | Every input platform has ≥1 chunk |

### Quality Metrics

| Metric | Target | ⚠️ Warning | ❌ Fail |
|---|---|---|---|
| **Total clean chunks** | ≥ 2,000 | 500–1,999 | < 500 |
| **PII matches in output** | 0 | — | ≥ 1 |
| **Deduplication rate** | 5–25% | > 25% (too much) | — |
| **Spam filter rate** | 10–40% | > 50% (too aggressive) | > 70% |
| **Relevance filter rate** | 10–30% | > 40% | > 60% |
| **Avg chunk word count** | 50–300 | 30–50 or 300–500 | < 30 or > 500 |
| **Max chunks from single record** | ≤ 30 | 31–50 | > 50 |
| **Language: % English** | ≥ 70% | 50–70% | < 50% |
| **Language: % Hindi/Hinglish** | ≤ 30% | — | — |
| **Language: % Other** | 0% | 1–5% | > 5% |

### Automated Test Script

```bash
#!/bin/bash
# Phase 2 Eval — run from backend/ directory
echo "=== Phase 2 Evaluation ==="

echo "[G2.1] Clean corpus exists..."
[ -f data/clean/corpus.jsonl ] && echo "✅ PASS" || { echo "❌ FAIL"; exit 1; }

echo "[G2.2] Chunk count..."
CHUNKS=$(wc -l < data/clean/corpus.jsonl)
if [ "$CHUNKS" -ge 500 ]; then echo "✅ PASS ($CHUNKS chunks)"
else echo "❌ FAIL ($CHUNKS chunks — need ≥500)"; fi

echo "[G2.3] PII scan..."
PII_EMAILS=$(grep -cP '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}' data/clean/corpus.jsonl 2>/dev/null || echo 0)
PII_HANDLES=$(grep -cP '"text".*@[A-Za-z_]\w{2,}' data/clean/corpus.jsonl 2>/dev/null || echo 0)
PII_PHONES=$(grep -cP '\b[6-9]\d{9}\b' data/clean/corpus.jsonl 2>/dev/null || echo 0)
PII_TOTAL=$((PII_EMAILS + PII_HANDLES + PII_PHONES))
[ "$PII_TOTAL" -eq 0 ] && echo "✅ PASS (0 PII matches)" || echo "❌ FAIL ($PII_TOTAL PII matches found)"

echo "[G2.4] Schema compliance..."
python -c "
import json
errors = 0
required = ['chunk_id', 'parent_record_id', 'source_platform', 'text', 'word_count']
for i, line in enumerate(open('data/clean/corpus.jsonl')):
    r = json.loads(line)
    for k in required:
        if k not in r:
            errors += 1; break
if errors == 0: print('✅ PASS')
else: print(f'❌ FAIL — {errors} chunks missing required fields')
"

echo "[G2.5] Exact duplicate check..."
python -c "
import json
texts = set()
dupes = 0
for line in open('data/clean/corpus.jsonl'):
    t = json.loads(line)['text']
    if t in texts: dupes += 1
    texts.add(t)
if dupes == 0: print('✅ PASS (0 exact duplicates)')
else: print(f'❌ FAIL ({dupes} exact duplicates)')
"

echo "[G2.6] Privacy log..."
[ -f reports/privacy_log.md ] && echo "✅ PASS" || echo "❌ FAIL — no privacy_log.md"

echo "[G2.7] Retention rate..."
RAW=$(cat data/raw/*.jsonl 2>/dev/null | wc -l)
python -c "
raw=$RAW; clean=$CHUNKS
rate = clean / raw if raw > 0 else 0
if 0.30 <= rate <= 0.80: print(f'✅ PASS ({rate:.1%} retained)')
elif 0.20 <= rate < 0.30 or 0.80 < rate <= 0.95: print(f'⚠️ WARNING ({rate:.1%} retained)')
else: print(f'❌ FAIL ({rate:.1%} retained — check filters)')
"

echo "[G2.8] Per-platform coverage..."
python -c "
import json
from collections import Counter
platforms = Counter()
for line in open('data/clean/corpus.jsonl'):
    platforms[json.loads(line)['source_platform']] += 1
print('  Platform distribution:')
for p, c in platforms.most_common():
    print(f'    {p}: {c} chunks')
empty = [p for p, c in platforms.items() if c == 0]
if not empty: print('✅ PASS — all platforms represented')
else: print(f'⚠️ WARNING — platforms with 0 chunks: {empty}')
"

echo "=== Phase 2 Complete ==="
```

### Manual Review Checklist

- [ ] Read 10 random chunks — do they make sense as standalone text?
- [ ] Verify no `[deleted]`, `[removed]`, or HTML tags in chunk text
- [ ] Check that chunks from Reddit are individual comments (not entire threads)
- [ ] Check that long reviews were split at sentence boundaries (no mid-sentence cuts)
- [ ] Review `reports/privacy_log.md` — do the PII counts look reasonable?
- [ ] Spot-check that `[REDACTED]` replacements don't appear excessively (> 5 per chunk)
- [ ] Verify Hinglish content is retained (not filtered as non-English)

### Failure Protocol

| Failure | Action |
|---|---|
| PII found in clean corpus | Fix PII stripper regex/NER. Re-run Phase 2. |
| < 500 chunks | Check filter rates — likely too aggressive. Lower relevance threshold. |
| Retention < 30% | Review spam filter and relevance filter rules. May need broader keyword list. |
| A platform has 0 chunks | Check if all its records were filtered. May need platform-specific filter tuning. |

---

## Phase 3: Thematic Analysis Engine

### Gate Criteria

| # | Criterion | Test | Pass Condition |
|---|---|---|---|
| G3.1 | Themes file exists | `wc -l data/themes/themes.jsonl` | 10–25 themes |
| G3.2 | Micro-themes file exists | `ls data/themes/micro_themes.jsonl` | File exists |
| G3.3 | All 10 RQs covered | `cat data/themes/rq_coverage.json` | `"uncovered": []` |
| G3.4 | Every theme has evidence | Check `chunk_count > 0` for all themes | 100% |
| G3.5 | Every theme has ≥1 verbatim snippet | Check `evidence` array is non-empty | 100% |
| G3.6 | Theme `chunk_ids` are valid | Cross-reference against `corpus.jsonl` | 100% valid IDs |
| G3.7 | No duplicate theme names | Unique names check | All unique |
| G3.8 | LLM batch success rate | Check logs | ≥ 95% |

### Quality Metrics

| Metric | Target | ⚠️ Warning | ❌ Fail |
|---|---|---|---|
| **Theme count** | 10–25 | 8–9 or 26–30 | < 8 or > 30 |
| **Micro-theme count** | 50–200 | 30–49 or 201–300 | < 30 or > 300 |
| **Avg evidence chunks per theme** | ≥ 50 | 20–49 | < 20 |
| **Min evidence chunks (any theme)** | ≥ 10 | 5–9 | < 5 |
| **RQ coverage** | 10/10 | 9/10 | < 9/10 |
| **Themes covering ≥ 2 RQs** | ≥ 30% | 15–30% | < 15% |
| **Multi-platform themes** (≥2 platforms) | ≥ 60% | 40–60% | < 40% |
| **LLM batch success rate** | ≥ 95% | 90–95% | < 90% |
| **Cache hit rate** (on re-runs) | ≥ 80% | — | — |
| **Invalid chunk_id rate** | 0% | 1–3% | > 3% |

### Automated Test Script

```bash
#!/bin/bash
# Phase 3 Eval — run from backend/ directory
echo "=== Phase 3 Evaluation ==="

echo "[G3.1] Theme count..."
THEMES=$(wc -l < data/themes/themes.jsonl 2>/dev/null || echo 0)
if [ "$THEMES" -ge 10 ] && [ "$THEMES" -le 25 ]; then echo "✅ PASS ($THEMES themes)"
elif [ "$THEMES" -ge 8 ] && [ "$THEMES" -le 30 ]; then echo "⚠️ WARNING ($THEMES themes — slightly out of range)"
else echo "❌ FAIL ($THEMES themes — expected 10–25)"; fi

echo "[G3.2] Micro-themes..."
[ -f data/themes/micro_themes.jsonl ] && echo "✅ PASS ($(wc -l < data/themes/micro_themes.jsonl) micro-themes)" || echo "❌ FAIL"

echo "[G3.3] RQ coverage..."
python -c "
import json
cov = json.load(open('data/themes/rq_coverage.json'))
uncovered = cov.get('uncovered', [])
if not uncovered: print('✅ PASS — all 10 RQs covered')
else: print(f'❌ FAIL — uncovered RQs: {uncovered}')
"

echo "[G3.4–G3.6] Theme quality..."
python -c "
import json

corpus_ids = set()
for line in open('data/clean/corpus.jsonl'):
    corpus_ids.add(json.loads(line)['chunk_id'])

issues = []
themes = [json.loads(l) for l in open('data/themes/themes.jsonl')]
for t in themes:
    if t.get('chunk_count', 0) == 0:
        issues.append(f\"{t['theme_id']}: zero chunks\")
    if not t.get('evidence'):
        issues.append(f\"{t['theme_id']}: no evidence snippets\")
    # Check chunk_id validity
    for ev in t.get('evidence', []):
        if ev.get('chunk_id') and ev['chunk_id'] not in corpus_ids:
            issues.append(f\"{t['theme_id']}: invalid chunk_id {ev['chunk_id']}\")

if not issues: print('✅ PASS — all themes valid')
else:
    print(f'❌ FAIL — {len(issues)} issues:')
    for i in issues[:10]: print(f'  • {i}')
"

echo "[G3.7] Duplicate theme names..."
python -c "
import json
names = [json.loads(l)['name'] for l in open('data/themes/themes.jsonl')]
dupes = [n for n in names if names.count(n) > 1]
if not dupes: print('✅ PASS')
else: print(f'❌ FAIL — duplicate names: {set(dupes)}')
"

echo "=== Phase 3 Complete ==="
```

### Manual Review Checklist

- [ ] Read every theme name — are they specific and actionable (not vague like "General Issues")?
- [ ] Read the top 3 evidence snippets per theme — do they genuinely support the theme?
- [ ] Check that no PII survived into evidence snippets
- [ ] Verify that research data themes are labeled with `source_platform: "interview"` or `"survey"`
- [ ] Are the top 5 themes intuitively the most important fashion wishlisting frictions?
- [ ] Do any themes overlap significantly? (Candidates for merging)
- [ ] Is the theme consolidation reasonable? (Not too aggressive, not too conservative)

### Failure Protocol

| Failure | Action |
|---|---|
| < 10 themes | LLM may be over-consolidating. Tune prompt: "Produce at least 12 distinct themes." |
| > 25 themes | LLM may be under-consolidating. Re-run Pass 2 with stronger merge instructions. |
| Uncovered RQ | Run `fill_gaps()`. If no evidence exists, document in the report. |
| Invalid chunk_ids | Phase 3 has a bug linking themes to chunks. Fix and re-run. |
| Vague theme names | Re-run consolidation with explicit prompt: "Each theme must name a SPECIFIC friction." |

---

## Phase 4: Opportunity Quantification & Prioritization

### Gate Criteria

| # | Criterion | Test | Pass Condition |
|---|---|---|---|
| G4.1 | Matrix file exists | `cat data/matrix/matrix.json` | Valid JSON, ≥10 themes |
| G4.2 | All themes have scores | Check `opportunity_score` exists for each | 100% |
| G4.3 | All scores in 0–100 range | Bounds check | No out-of-range values |
| G4.4 | Themes are ranked | Check `rank` field, contiguous 1..N | All ranks present |
| G4.5 | Opportunity report exists | `wc -w reports/opportunity_report.md` | > 1,000 words |
| G4.6 | Report covers all 10 RQs | Search for RQ1–RQ10 in report | All present |
| G4.7 | Segment view exists | `cat reports/segment_view.md` | File exists |
| G4.8 | No segment below min sample size | Check `segment_cuts` in matrix.json | All segments ≥ 10 chunks (or flagged `low_confidence`) |

### Quality Metrics

| Metric | Target | ⚠️ Warning | ❌ Fail |
|---|---|---|---|
| **Score range (max – min)** | ≥ 20 points | 10–19 | < 10 (flat) |
| **Score standard deviation** | ≥ 10 | 5–10 | < 5 |
| **Purchase-delay score variation** | std dev ≥ 8 | 4–8 | < 4 (LLM gave uniform scores) |
| **Frequency score max** | ≥ 30 | 15–30 | < 15 (no dominant theme) |
| **Report word count** | ≥ 3,000 | 1,000–3,000 | < 1,000 |
| **Themes with ≥3 evidence quotes** | 100% | 80–99% | < 80% |
| **Segment dimensions with data** | ≥ 2 of 4 | 1 | 0 |
| **Segments flagged `low_confidence`** | ≤ 30% | 31–50% | > 50% |

### Automated Test Script

```bash
#!/bin/bash
# Phase 4 Eval — run from backend/ directory
echo "=== Phase 4 Evaluation ==="

echo "[G4.1] Matrix file..."
python -c "
import json
m = json.load(open('data/matrix/matrix.json'))
themes = m if isinstance(m, list) else m.get('themes', [])
print(f'✅ PASS ({len(themes)} themes)') if len(themes) >= 10 else print(f'❌ FAIL ({len(themes)} themes)')
"

echo "[G4.2-4.4] Scores and ranks..."
python -c "
import json
themes = json.load(open('data/matrix/matrix.json'))
if not isinstance(themes, list): themes = themes.get('themes', [])

issues = []
scores = []
for t in themes:
    s = t.get('opportunity_score')
    if s is None: issues.append(f\"{t['theme_id']}: missing score\")
    elif not (0 <= s <= 100): issues.append(f\"{t['theme_id']}: score {s} out of range\")
    else: scores.append(s)
    if 'rank' not in t: issues.append(f\"{t['theme_id']}: missing rank\")

if not issues:
    spread = max(scores) - min(scores)
    print(f'✅ PASS — score range: {min(scores):.1f}–{max(scores):.1f} (spread: {spread:.1f})')
else:
    print(f'❌ FAIL — {len(issues)} issues:')
    for i in issues[:5]: print(f'  • {i}')
"

echo "[G4.5] Opportunity report..."
[ -f reports/opportunity_report.md ] && {
    WORDS=$(wc -w < reports/opportunity_report.md)
    [ "$WORDS" -ge 1000 ] && echo "✅ PASS ($WORDS words)" || echo "❌ FAIL ($WORDS words — too short)"
} || echo "❌ FAIL — file missing"

echo "[G4.6] RQ coverage in report..."
MISSING_RQ=0
for rq in RQ1 RQ2 RQ3 RQ4 RQ5 RQ6 RQ7 RQ8 RQ9 RQ10; do
    grep -qi "$rq" reports/opportunity_report.md || { echo "  ⚠️ Missing: $rq"; MISSING_RQ=$((MISSING_RQ+1)); }
done
[ "$MISSING_RQ" -eq 0 ] && echo "✅ PASS — all 10 RQs present" || echo "❌ FAIL — $MISSING_RQ RQs missing"

echo "[G4.7] Segment view..."
[ -f reports/segment_view.md ] && echo "✅ PASS" || echo "❌ FAIL"

echo "[G4.8] Segment sample sizes..."
python -c "
import json
themes = json.load(open('data/matrix/matrix.json'))
if not isinstance(themes, list): themes = themes.get('themes', [])

low_conf = 0
violations = 0
for t in themes:
    for dim, cats in t.get('segment_cuts', {}).items():
        for cat, count in cats.items():
            if isinstance(count, dict):
                c = count.get('count', count.get('chunk_count', 0))
                lc = count.get('low_confidence', False)
            else:
                c = count; lc = False
            if c < 10 and not lc: violations += 1
            if c < 10: low_conf += 1
if violations == 0: print(f'✅ PASS (all segments ≥10 chunks or flagged)')
else: print(f'❌ FAIL ({violations} segments below threshold without low_confidence flag)')
"

echo "=== Phase 4 Complete ==="
```

### Manual Review Checklist

- [ ] Does the #1 ranked theme feel intuitively correct as the top opportunity?
- [ ] Read the executive summary of the report — is it clear and actionable?
- [ ] Are evidence quotes real and specific (not generic)?
- [ ] Are segment breakdowns intuitive? (e.g., "women_western" and "footwear" should both appear)
- [ ] Do any themes feel artificially inflated by a single platform? (Check platform_distribution)
- [ ] Is the scoring spread sufficient to meaningfully rank themes?

### Failure Protocol

| Failure | Action |
|---|---|
| Flat scores (spread < 10) | Re-prompt LLM for purchase-delay scoring with "scores must vary across themes" |
| Report missing RQs | Check `rq_coverage.json`. Run `fill_gaps()` if needed. |
| Segments below threshold | Either flag as `low_confidence` or merge into broader categories |
| Report too short | Check `_generate_opportunity_report()` — may need richer template |

---

## Phase 5: RAG Assistant + Web Application

### Gate Criteria

| # | Criterion | Test | Pass Condition |
|---|---|---|---|
| G5.1 | Vector store built | `ls data/vectorstore/` | Directory has files |
| G5.2 | Both collections exist | ChromaDB collection list | `corpus_chunks` + `theme_summaries` |
| G5.3 | Reranker model loads | Import + score test pair | Non-error response |
| G5.4 | FastAPI starts locally | `curl http://localhost:8000/api/health` | `{"status": "ok"}` |
| G5.5 | Next.js starts locally | Open `http://localhost:3000` | Page renders |
| G5.6 | Query returns cited response | POST `/api/query` | Response contains `[Source: ...]` |
| G5.7 | Streaming works | SSE test | Incremental text delivery |
| G5.8 | Citation validation catches fakes | Test with fabricated chunk_id | Flagged as hallucinated |
| G5.9 | Railway deployment works | Hit production health endpoint | `{"status": "ok"}` |
| G5.10 | Vercel deployment works | Open production URL | Page renders |
| G5.11 | CORS works in production | Frontend → Backend API call | No CORS error |
| G5.12 | Retrieval benchmark passes | Run evaluator | Recall@5 ≥ 0.70, MRR ≥ 0.60 |

### Quality Metrics — Retrieval

| Metric | Target | ⚠️ Warning | ❌ Fail |
|---|---|---|---|
| **Recall@5 (overall)** | ≥ 0.70 | 0.55–0.69 | < 0.55 |
| **Recall@10 (overall)** | ≥ 0.85 | 0.70–0.84 | < 0.70 |
| **MRR (overall)** | ≥ 0.60 | 0.45–0.59 | < 0.45 |
| **Reranker lift (Recall@5)** | ≥ +10% | +5%–+9% | ≤ 0% (negative) |
| **Recall@5 (English queries)** | ≥ 0.75 | 0.60–0.74 | < 0.60 |
| **Recall@5 (Hindi queries)** | ≥ 0.50 | 0.35–0.49 | < 0.35 |
| **Recall@5 (Hinglish queries)** | ≥ 0.55 | 0.40–0.54 | < 0.40 |

### Quality Metrics — Generation

| Metric | Target | ⚠️ Warning | ❌ Fail |
|---|---|---|---|
| **Citation rate** (% responses with ≥1 citation) | 100% | 90–99% | < 90% |
| **Hallucinated citation rate** | 0% | 1–3% | > 3% |
| **Out-of-scope rejection rate** (correctly refuses) | 100% | — | < 80% |
| **Average response time** | < 10s | 10–20s | > 20s |
| **PII in generated responses** | 0 | — | ≥ 1 |
| **Streaming success rate** | ≥ 98% | 95–98% | < 95% |

### Automated Test Script

```bash
#!/bin/bash
# Phase 5 Eval — run from backend/ directory
echo "=== Phase 5 Evaluation ==="

echo "[G5.1] Vector store..."
[ -d data/vectorstore ] && [ "$(ls data/vectorstore/ | wc -l)" -gt 0 ] && echo "✅ PASS" || echo "❌ FAIL"

echo "[G5.2] Collections..."
python -c "
import chromadb
client = chromadb.PersistentClient(path='data/vectorstore')
collections = [c.name for c in client.list_collections()]
if 'corpus_chunks' in collections and 'theme_summaries' in collections:
    print(f'✅ PASS — {collections}')
else:
    print(f'❌ FAIL — found: {collections}, expected corpus_chunks + theme_summaries')
"

echo "[G5.4] FastAPI health..."
HEALTH=$(curl -s http://localhost:8000/api/health 2>/dev/null)
echo "$HEALTH" | grep -q "ok" && echo "✅ PASS" || echo "❌ FAIL — $HEALTH"

echo "[G5.6] Query test..."
RESPONSE=$(curl -s -X POST http://localhost:8000/api/query \
    -H "Content-Type: application/json" \
    -d '{"query": "Why do users add items to their wishlist?", "stream": false}')
echo "$RESPONSE" | grep -q "\[Source:" && echo "✅ PASS — citations present" || echo "❌ FAIL — no citations"

echo "[G5.6b] Out-of-scope rejection..."
OOS=$(curl -s -X POST http://localhost:8000/api/query \
    -H "Content-Type: application/json" \
    -d '{"query": "What is the weather today?", "stream": false}')
echo "$OOS" | grep -qi "insufficient\|don't have\|cannot answer\|not.*information" && echo "✅ PASS — correctly rejected" || echo "⚠️ WARNING — may have answered an out-of-scope query"

echo "[G5.6c] PII check on response..."
echo "$RESPONSE" | grep -cP '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}' | grep -q "^0$" && echo "✅ PASS — no PII" || echo "❌ FAIL — PII detected in response"

echo "=== Phase 5 Complete ==="
```

### Retrieval Benchmark Test

```bash
#!/bin/bash
# Run the full retrieval benchmark
echo "=== Retrieval Benchmark ==="

python -c "
from src.rag.evaluator import RetrievalEvaluator
from src.rag.retriever import Retriever
from src.rag.rag_config import RAGConfig

config = RAGConfig()
# ... initialize components ...
evaluator = RetrievalEvaluator(retriever, 'data/eval/benchmark_queries.json')
results = evaluator.evaluate()
report = evaluator.generate_report(results)

# Print summary
overall = results['overall']
print(f\"Recall@5:  {overall['recall_at_5']:.3f}  {'✅' if overall['recall_at_5'] >= 0.70 else '❌'}\")
print(f\"Recall@10: {overall['recall_at_10']:.3f}  {'✅' if overall['recall_at_10'] >= 0.85 else '❌'}\")
print(f\"MRR:       {overall['mrr']:.3f}  {'✅' if overall['mrr'] >= 0.60 else '❌'}\")

# Reranker lift
lift = results.get('reranker_lift', {})
print(f\"Reranker lift: {lift.get('lift', 'N/A')}  {'✅' if '+' in str(lift.get('lift','')) else '⚠️'}\")

# Per-language
for lang, metrics in results.get('by_language', {}).items():
    print(f\"  {lang}: Recall@5={metrics['recall_at_5']:.3f}\")
"
```

### Test Query Matrix

| # | Query | Language | Expected Behavior | Pass Criteria |
|---|---|---|---|---|
| 1 | "Why do users add items to their wishlist?" | EN | Returns RQ1-tagged evidence | ≥1 citation, themes match RQ1 |
| 2 | "What prevents users from buying wishlisted items?" | EN | Returns RQ2 evidence | ≥2 citations from different platforms |
| 3 | "How do size and fit concerns affect purchases?" | EN | Returns RQ3+RQ7 evidence | Citations reference size/fit themes |
| 4 | "Do users use the wishlist as a bookmark?" | EN | Returns RQ8 evidence | Distinguishes intent vs. bookmarking |
| 5 | "What do users search for outside Myntra?" | EN | Returns RQ6 evidence | Mentions external research behavior |
| 6 | "myntra pe wishlist mein kyun rakhte ho?" | HI | Returns RQ1 evidence (Hindi) | ≥1 citation, relevant content |
| 7 | "why myntra ki wishlist se kuch nahi khareedta" | Hinglish | Returns RQ2 evidence | ≥1 citation, relevant content |
| 8 | "What is the weather today?" | EN (off-topic) | Refuses to answer | Contains "insufficient" or equivalent |
| 9 | "Tell me about Flipkart's delivery" | EN (tangential) | Refuses or answers cautiously | Low-confidence or refusal |
| 10 | "" (empty query) | — | Returns 400 error | HTTP 400, no crash |

### Manual Review Checklist

- [ ] Chat interface renders correctly on desktop and mobile
- [ ] Streaming responses appear word-by-word (not as a single dump)
- [ ] Citation cards show platform badge, text snippet, and chunk ID
- [ ] Clicking a citation expands to show full source context
- [ ] Report page renders the opportunity report with proper formatting
- [ ] Matrix page shows an interactive chart with clickable themes
- [ ] Out-of-scope queries get a polite refusal
- [ ] Response time is < 15s for typical queries on production
- [ ] Cold start on Railway is < 30s

### Failure Protocol

| Failure | Action |
|---|---|
| Recall@5 < 0.55 | Investigate: chunk size, embedding model, query prefix. Consider BGE-base. |
| Reranker negative lift | Disable reranker (`RERANKER_ENABLED=False`). Use BGE-only ranking. |
| Hindi Recall@5 < 0.35 | Add query translation (Hindi → English) pre-processing. |
| Citation rate < 90% | Strengthen system prompt. Add citation instruction as user message suffix. |
| PII in responses | Fix PII scan on generated responses. Add response-level PII filter. |
| CORS errors in prod | Verify `FRONTEND_URL` env var on Railway matches Vercel URL. |
| Railway OOM | Profile memory. Lazy-load models. Consider FAISS over ChromaDB. |

---

## Phase 6: Reports, Documentation & Final Verification

### Gate Criteria

| # | Criterion | Test | Pass Condition |
|---|---|---|---|
| G6.1 | Opportunity report polished | Manual review | All 10 RQs answered with evidence |
| G6.2 | Segment view polished | Manual review | Segments labeled, thin data flagged |
| G6.3 | Privacy log complete | Manual review | All PII stripping documented |
| G6.4 | README exists | `cat README.md` | Setup instructions, architecture, limitations |
| G6.5 | Makefile works | `make install && make all` | All targets execute |
| G6.6 | Final PII sweep clean | Regex scan all outputs | Zero findings |
| G6.7 | All 6 success criteria pass | Verification matrix | All 6 pass |
| G6.8 | Both deployments live | Hit production URLs | Frontend + backend respond |

### Success Criteria Verification Matrix

| # | Success Criterion | Verification Method | Pass Condition | Status |
|---|---|---|---|---|
| SC1 | Report answers all 10 RQs with evidence | Search report for RQ1–RQ10 | Each has ≥1 theme with ≥1 evidence quote | ☐ |
| SC2 | Opportunity areas ranked and quantified | Check `matrix.json` | All themes have scores, ranks, composite > 0 | ☐ |
| SC3 | Every theme and RAG answer traceable to real snippet | Theme evidence has `chunk_id`; RAG has `[Source:]` | 100% traceability | ☐ |
| SC4 | Entire build runs within free-tier tools | Audit API usage logs | No paid API calls, no paid infra | ☐ |
| SC5 | No PII in stored data, reports, or RAG responses | Regex scan all output files | Zero findings | ☐ |
| SC6 | Output specific enough for follow-on solution design | Stakeholder review | Themes are actionable, not vague | ☐ |

### Final PII Sweep

```bash
#!/bin/bash
# Final PII Sweep — run from backend/ directory
echo "=== Final PII Sweep ==="

FINDINGS=0

echo "Checking for email addresses..."
COUNT=$(grep -rcP '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}' data/ reports/ 2>/dev/null | grep -v ":0$" | wc -l)
FINDINGS=$((FINDINGS + COUNT))
[ "$COUNT" -eq 0 ] && echo "✅ Emails: clean" || echo "❌ Emails: found in $COUNT files"

echo "Checking for @handles..."
COUNT=$(grep -rcP '(?<!\w)@[A-Za-z_]\w{2,}' data/ reports/ 2>/dev/null | grep -v ":0$" | wc -l)
FINDINGS=$((FINDINGS + COUNT))
[ "$COUNT" -eq 0 ] && echo "✅ Handles: clean" || echo "❌ Handles: found in $COUNT files"

echo "Checking for phone numbers..."
COUNT=$(grep -rcP '\b[6-9]\d{9}\b' data/ reports/ 2>/dev/null | grep -v ":0$" | wc -l)
FINDINGS=$((FINDINGS + COUNT))
[ "$COUNT" -eq 0 ] && echo "✅ Phones: clean" || echo "❌ Phones: found in $COUNT files"

echo "Checking for Reddit usernames..."
COUNT=$(grep -rcP '(?:u/|user/)[A-Za-z0-9_-]+' data/ reports/ 2>/dev/null | grep -v ":0$" | wc -l)
FINDINGS=$((FINDINGS + COUNT))
[ "$COUNT" -eq 0 ] && echo "✅ Reddit users: clean" || echo "❌ Reddit users: found in $COUNT files"

echo ""
if [ "$FINDINGS" -eq 0 ]; then
    echo "✅ FINAL PII SWEEP: CLEAN"
else
    echo "❌ FINAL PII SWEEP: $FINDINGS FILES WITH POTENTIAL PII"
    echo "   ACTION: Fix PII stripper, re-run Phase 2+, and re-sweep."
fi

echo "=== Sweep Complete ==="
```

### Manual Review Checklist

- [ ] Read the executive summary of the opportunity report — would a PM find it actionable?
- [ ] Are all theme deep-dives specific enough to inspire concrete solution ideas?
- [ ] Does the segment view make sense? (No impossible segments like "men_ethnic: lehenga")
- [ ] Does the README have clear setup steps that a new developer could follow?
- [ ] Are known limitations documented honestly?
- [ ] Is the Makefile tested end-to-end (`make all`)?
- [ ] Is the privacy log human-readable and complete?
- [ ] Are both production URLs (Vercel + Railway) working?
- [ ] Does the RAG assistant answer the 10 test queries well in production?

---

## Summary: Phase Gate Scorecard

Use this table to track phase completion:

| Phase | Total Gates | Critical Gates | Status | Date Passed |
|---|---|---|---|---|
| **Phase 0** — Setup | 15 | G0.8, G0.9, G0.15 | ☐ | |
| **Phase 1** — Ingestion | 8 | G1.2, G1.5, G1.6 | ☐ | |
| **Phase 2** — Cleaning | 8 | G2.2, G2.3, G2.7 | ☐ | |
| **Phase 3** — Analysis | 8 | G3.1, G3.3, G3.6 | ☐ | |
| **Phase 4** — Quantification | 8 | G4.2, G4.3, G4.6 | ☐ | |
| **Phase 5** — RAG + Web App | 12 | G5.6, G5.8, G5.12 | ☐ | |
| **Phase 6** — Reports & Verification | 8 | G6.6, G6.7, G6.8 | ☐ | |
| **Total** | **67** | **18** | | |

> **Rule:** A phase cannot exit until ALL gate criteria pass (✅). Warning (⚠️) conditions are acceptable but must be documented. Failures (❌) block phase exit.
