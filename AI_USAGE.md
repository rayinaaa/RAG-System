# AI Usage Disclosure

This project was built with assistance from OpenAI Codex inside the local development workspace.

## AI Tools Used

- OpenAI Codex was used to generate, revise, and validate code and documentation.
- The assistant used local terminal commands to inspect files, run build checks, and verify backend/frontend behavior.

## How AI Was Used

- Scaffolding the FastAPI backend, React frontend, and RAG modules.
- Implementing parsing, chunking, retrieval, reranking, prompt building, citations, streaming, and dashboard features.
- Implementing query understanding, explainability payloads, confidence labels, document insights, and Gemini REST error handling.
- Drafting documentation, API docs, architecture notes, setup instructions, tests, Docker files, and this disclosure.
- Running compile/build checks and iterating on implementation issues.

## Manual Engineering Decisions

The following decisions were intentionally selected based on the assignment requirements and engineering judgment:

- ChromaDB was used for local persistent vector storage because it keeps the project simple to run while supporting metadata filtering.
- `BAAI/bge-small-en-v1.5` was selected because it is small enough for local use and strong enough for English semantic retrieval.
- Hybrid retrieval was implemented because vector search and keyword search solve different failure modes.
- Reranking was added to improve final context quality before sending chunks to Gemini.
- Server-Sent Events were used for chat and document updates because they are simpler than WebSockets for one-way streaming.
- Configuration was centralized through environment variables to avoid hardcoded deployment behavior.

## Reviewed And Modified By Developer

The implementation was reviewed and modified for:

- Input validation and clearer user-facing errors.
- Real-time streaming behavior.
- Thread-safe document update subscriptions.
- Retrieval fallback behavior.
- UI readiness states and source previews.
- Explainability UX and confidence reporting.
- Documentation clarity and evaluation readiness.
