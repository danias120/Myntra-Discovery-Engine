FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    OMP_NUM_THREADS=1 \
    MKL_NUM_THREADS=1 \
    TORCH_NUM_THREADS=1 \
    HF_HUB_DISABLE_SYMLINKS_WARNING=1 \
    TRANSFORMERS_NO_ADVISORY_WARNINGS=1 \
    PORT=8000

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt ./backend/requirements.txt
RUN python -m pip install --no-cache-dir --upgrade pip && \
    python -m pip install --no-cache-dir -r backend/requirements.txt && \
    python -m spacy download en_core_web_sm

# Pre-cache Hugging Face embedding & cross-encoder models into container image at build time
RUN python -c "from sentence_transformers import SentenceTransformer, CrossEncoder; SentenceTransformer('BAAI/bge-small-en-v1.5'); CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')"

# Copy application source code and pre-indexed Chroma vectorstore
COPY backend ./backend
COPY Docs ./Docs
COPY reports ./reports

WORKDIR /app/backend

EXPOSE 8000

CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
