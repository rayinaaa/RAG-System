# Architecture And Implementation Decisions

This project is designed around five priorities: clarity, correctness, retrieval quality, real-time feedback, and maintainability.

## Request Flow

1. Users upload PDF, DOCX, TXT, or CSV files from the React UI.
2. FastAPI saves the original files under `backend/uploads/`.
3. A background processing task extracts text, cleans it, chunks it, embeds it, and stores vectors plus metadata in ChromaDB.
4. The UI receives document status updates through `GET /documents/events` using Server-Sent Events.
5. When a user asks a question, the backend classifies the query, expands it when useful, runs hybrid retrieval, reranks the best candidates, builds a grounded prompt, and returns a Gemini-backed answer.
6. The final chat event includes citations, confidence, query understanding, retrieved evidence, and timing metadata.

## Retrieval Design

The retriever combines two complementary search methods:

- Vector search handles semantic similarity and paraphrased questions.
- BM25 handles exact terms, table values, policy names, and identifiers.

Scores are merged with:

```text
final_score = 0.7 * vector_score + 0.3 * keyword_score
```

The top 20 hybrid results are sent through a cross-encoder reranker, and only the top 5 chunks are included in the LLM prompt. This keeps prompts focused and reduces citation drift.

Before retrieval, `rag/query_understanding.py` classifies the user request into search, summary, comparison, or follow-up. It also expands common abbreviations and follow-up phrasing. This is deterministic by design so retrieval remains inspectable and testable without another LLM call.

## Grounding And Citations

The prompt builder gives Gemini strict rules:

- Use only retrieved context.
- Do not invent missing information.
- Cite factual statements with source numbers.
- Return `Information not found in uploaded documents.` when context is insufficient.

The backend also returns structured source metadata from the same retrieved chunks, so the UI can show citations independently of the answer text.

The answer verifier enforces a final guardrail: if retrieval confidence is too low or the answer has no usable citations, the system returns a low-confidence not-found response instead of presenting unsupported claims.

## Explainability Flow

The chat response contains an `explanation` object with:

- query classification and expanded queries
- the retrieved chunks shown to the model
- vector, BM25, fused, and reranker scores
- final context sent to Gemini

The frontend exposes this through a "Why this answer?" panel so reviewers can inspect the RAG decision path rather than treating the answer as a black box.

## Real-Time Behavior

Two real-time channels are used:

- `POST /chat/stream`: emits retrieval progress, answer content, completion metadata, and structured errors over Server-Sent Events.
- `GET /documents/events`: streams document upload, processing, failure, ready, and delete updates.

The frontend keeps a polling fallback for document updates only if the SSE connection drops.

## Correctness Decisions

- Uploaded files are validated by extension before storage.
- Document IDs and chunk IDs use UUIDs to avoid collisions.
- Model caches are kept under `backend/vectordb/model_cache` to avoid user-directory permission issues.
- Document metadata and metrics are persisted as JSON for local development clarity.
- Session memory is intentionally process-local; production multi-worker deployments should move it to Redis or a database.
- Live document subscribers are protected by a separate lock from document metadata, keeping file-state mutations and event delivery concerns separate.

## Code Quality Boundaries

The code is split by responsibility:

- `routes/`: HTTP surface and streaming endpoints
- `services/`: configuration, logging, storage, sessions, metrics, Gemini integration
- `rag/`: parsing, chunking, embedding, retrieval, reranking, prompt building, citation building
- `frontend/src/hooks/`: React stateful workflows
- `frontend/src/services/`: API and streaming clients
- `frontend/src/components/`: reusable UI

This separation keeps the RAG pipeline testable and makes it easier to replace individual pieces, such as Gemini, ChromaDB, reranker, or session storage.

## Production Hardening Path

For a larger deployment, the next improvements would be:

- Move document metadata, sessions, and metrics to PostgreSQL or Redis.
- Store uploads in object storage.
- Add authentication and per-user document isolation.
- Add background workers with a queue for document processing.
- Add automated evaluation sets for retrieval and citation accuracy.
- Add request tracing around retrieval, reranking, LLM generation, and streaming.
