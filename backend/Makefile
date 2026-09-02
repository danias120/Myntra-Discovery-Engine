.PHONY: install ingest clean analyze quantify rag-build api-dev all report deploy-backend deploy-frontend

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
