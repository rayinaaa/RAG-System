# API Documentation

Base URL: `http://127.0.0.1:8001`

## GET `/health`

Returns service health and dashboard metrics.

Response:

```json
{
  "status": "ok",
  "metrics": {
    "total_documents": 1,
    "total_chunks": 42,
    "average_retrieval_time_ms": 120.5,
    "average_generation_time_ms": 980.2,
    "average_confidence": 0.82,
    "retrieval_success_rate": 0.91,
    "total_queries_processed": 7
  }
}
```

## POST `/upload`

Uploads one or more documents. Supported extensions: `.pdf`, `.docx`, `.txt`, `.csv`.

Request: `multipart/form-data`

Field:

- `files`: one or more files

Response:

```json
[
  {
    "id": "uuid",
    "filename": "EmployeeHandbook.pdf",
    "path": "backend/uploads/uuid.pdf",
    "status": "queued",
    "progress": 5,
    "chunk_count": 0,
    "error": null,
    "created_at": "2026-06-07T00:00:00Z"
  }
]
```

Processing runs in the background. Poll `GET /documents` for status and progress.

## GET `/documents`

Lists uploaded documents and processing state.

## GET `/documents/events`

Streams live document updates with Server-Sent Events.

Events:

- `snapshot`: initial document list
- `document_added`: a document was uploaded
- `document_updated`: processing status, progress, chunk count, or error changed
- `document_deleted`: a document was removed
- `ping`: keep-alive event

Example:

```text
event: document_updated
data: {"event":"document_updated","documents":[...]}
```

## GET `/documents/{id}/summary`

Returns extractive document insights for an indexed document.

Response:

```json
{
  "document_id": "uuid",
  "filename": "EmployeeHandbook.pdf",
  "summary": "The document describes employee leave policy...",
  "suggested_questions": [
    "What are the main points in this document?",
    "What requirements or policies are described?"
  ],
  "key_topics": ["Requirements", "Timeline"],
  "important_dates": ["June 8, 2026"],
  "action_items": ["Review the submission requirements."]
}
```

## DELETE `/documents/{id}`

Deletes the stored file, document metadata, and associated ChromaDB vectors.

Response:

```json
{ "deleted": true, "id": "uuid" }
```

## POST `/chat`

Non-streaming RAG chat.

Request:

```json
{
  "message": "How many annual leaves are employees entitled to?",
  "session_id": "optional-session-id"
}
```

Response:

```json
{
  "session_id": "session-id",
  "answer": "Employees are entitled to 12 annual leaves per year. [1]",
  "sources": [
    {
      "number": 1,
      "filename": "EmployeeHandbook.pdf",
      "page_number": 4,
      "section_title": "Leave Policy",
      "chunk_id": "chunk-uuid"
    }
  ],
  "retrieval_ms": 130.4,
  "generation_ms": 812.2,
  "confidence": 0.86,
  "confidence_label": "high",
  "explanation": {
    "query_understanding": {
      "query_type": "search",
      "expanded_queries": ["How many annual leaves are employees entitled to?"],
      "rationale": "Direct search intent detected."
    },
    "retrieved_chunks": [
      {
        "citation_number": 1,
        "filename": "EmployeeHandbook.pdf",
        "page_number": 4,
        "section_title": "Leave Policy",
        "chunk_id": "chunk-uuid",
        "text": "Employees are entitled to 12 annual leaves per year...",
        "vector_score": 0.88,
        "keyword_score": 0.71,
        "final_score": 0.83,
        "rerank_score": 6.24
      }
    ],
    "context": "[1] EmployeeHandbook.pdf, Page 4..."
  }
}
```

## POST `/chat/stream`

Streaming-style RAG chat using Server-Sent Events over a POST request. Retrieval and reranking run first, then the backend emits retrieval progress, answer content, completion metadata, or a structured error.

Each event is emitted as:

```text
data: {"type":"token","token":"Employees "}
```

Retrieval completion event:

```text
data: {"type":"retrieval_done","retrieval_ms":130.4}
```

Completion event:

```text
data: {"type":"done","payload":{...ChatResponse}}
```

Error event:

```text
data: {"type":"error","error":"message"}
```

## Retrieval Pipeline

1. Parse documents with PyMuPDF, python-docx, pandas, or text decoding.
2. Clean extracted text and preserve filename, page number, section title, and chunk id.
3. Chunk with `chunk_size=500` and `chunk_overlap=100`.
4. Embed chunks with `BAAI/bge-small-en-v1.5`.
5. Store vectors and metadata in persistent ChromaDB.
6. Classify the query and generate deterministic query expansions.
7. Run vector search and BM25 keyword search for expanded queries.
8. Merge with `0.7 * vector_score + 0.3 * keyword_score`.
9. Return top 20 chunks to `cross-encoder/ms-marco-MiniLM-L-6-v2`.
10. Send top 5 reranked chunks to Gemini with strict citation instructions.
11. Verify that answers include citations or return a low-confidence not-found response.
