.PHONY: help install ingest clean analyze quantify rag-build eval api-dev all report deploy-backend deploy-frontend

help:
	@echo "Myntra Discovery Engine Backend Targets:"
	@echo "  make install        Install Python dependencies and SpaCy model"
	@echo "  make ingest         Run Stage 1 Ingestion across all sources"
	@echo "  make clean          Run Stage 2 PII Stripping, Spam Filtering, Dedup"
	@echo "  make analyze        Run Stage 3 Thematic Extraction & Consolidation"
	@echo "  make quantify       Run Stage 4 Opportunity Scoring & Matrix"
	@echo "  make rag-build      Run Stage 5 Vector Indexing with BGE-small"
	@echo "  make eval           Run Stage 5.8b Retrieval Evaluation Benchmark"
	@echo "  make api-dev        Start FastAPI development server on port 8000"
	@echo "  make all            Run Stages 1-5 end-to-end"
	@echo "  make report         Regenerate opportunity and segment reports"

install:
	pip install -r requirements.txt
	python -m spacy download en_core_web_sm

ingest:
	python pipeline.py --ingest

clean:
	python pipeline.py --clean

analyze:
	python pipeline.py --analyze

quantify:
	python pipeline.py --quantify

rag-build:
	python pipeline.py --rag-build

eval:
	python -m src.rag.evaluator --report

pii-sweep:
	python src/cleaning/pii_sweep.py

api-dev:
	uvicorn api.main:app --reload --port 8000

all:
	python pipeline.py --all

report:
	python pipeline.py --quantify

deploy-backend:
	railway up

deploy-frontend:
	cd ../frontend && vercel deploy --prod
