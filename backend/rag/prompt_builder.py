from backend.models.schemas import ChatMessage, RetrievedChunk


SYSTEM_PROMPT = """You are an AI document assistant.

Rules:
1. Answer only using the provided context.
2. Never make up information.
3. If the answer is not available in context, respond: 'Information not found in uploaded documents.'
4. Cite every factual statement.
5. Use concise and professional language.
6. Prefer direct evidence over broad summaries.
7. If the context is weak or indirect, say the information is not confidently found."""


def build_prompt(query: str, chunks: list[RetrievedChunk], history: list[ChatMessage]) -> str:
    context_blocks = []
    for index, chunk in enumerate(chunks, start=1):
        page = f", Page {chunk.metadata.page_number}" if chunk.metadata.page_number else ""
        section = f", Section: {chunk.metadata.section_title}" if chunk.metadata.section_title else ""
        context_blocks.append(
            f"[{index}] Source: {chunk.metadata.filename}{page}{section}\n"
            f"Chunk ID: {chunk.metadata.chunk_id}\n"
            f"{chunk.text}"
        )

    chat_history = "\n".join(f"{message.role}: {message.content}" for message in history[-8:])
    context = "\n\n".join(context_blocks) if context_blocks else "No relevant context was retrieved."

    return f"""{SYSTEM_PROMPT}

Citation format:
- End every factual sentence with a citation like [1].
- Only cite source numbers present in the retrieved context.
- Add a final "Sources:" section listing the sources used.

Chat history:
{chat_history or "No prior messages."}

Retrieved context:
{context}

User query:
{query}

Answer:"""
