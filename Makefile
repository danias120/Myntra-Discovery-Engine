.PHONY: help install ingest clean analyze quantify rag-build eval api-dev frontend-dev dev all report deploy-backend deploy-frontend

help:
	@echo "Myntra Wishlist Discovery Engine — Convenience Commands"
	@echo "========================================================"
	@echo "  make install         Install backend and frontend dependencies"
	@echo "  make dev             Run both backend and frontend locally"
	@echo "  make api-dev         Run FastAPI backend on port 8000"
	@echo "  make frontend-dev    Run Next.js frontend on port 3000"
	@echo "  make eval            Run Phase 5.8b retrieval benchmark"
	@echo "  make all             Run end-to-end data pipeline"
	@echo "  make deploy-backend  Deploy backend to Railway"
	@echo "  make deploy-frontend Deploy frontend to Vercel"

install:
	cd backend && $(MAKE) install
	cd frontend && npm install

dev:
	@echo "Launching backend on :8000 and frontend on :3000..."
	(cd backend && uvicorn api.main:app --reload --port 8000) & (cd frontend && npm run dev)

api-dev:
	cd backend && $(MAKE) api-dev

frontend-dev:
	cd frontend && npm run dev

eval:
	cd backend && $(MAKE) eval

pii-sweep:
	cd backend && $(MAKE) pii-sweep

ingest:
	cd backend && $(MAKE) ingest

clean:
	cd backend && $(MAKE) clean

analyze:
	cd backend && $(MAKE) analyze

quantify:
	cd backend && $(MAKE) quantify

rag-build:
	cd backend && $(MAKE) rag-build

all:
	cd backend && $(MAKE) all

report:
	cd backend && $(MAKE) report

deploy-backend:
	cd backend && $(MAKE) deploy-backend

deploy-frontend:
	cd frontend && vercel deploy --prod
