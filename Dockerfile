FROM python:3.12-slim AS backend

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV MODEL_LOCAL_FILES_ONLY=true
ENV MODEL_CACHE_DIR=/app/backend/vectordb/model_cache

RUN apt-get update && apt-get install -y --no-install-recommends build-essential curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend ./backend
COPY .env.example ./.env.example

RUN python -c "from pathlib import Path; from sentence_transformers import SentenceTransformer, CrossEncoder; cache=Path('/app/backend/vectordb/model_cache'); SentenceTransformer('BAAI/bge-small-en-v1.5', cache_folder=str(cache / 'sentence_transformers')); CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2', cache_dir=str(cache / 'transformers'))"

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
