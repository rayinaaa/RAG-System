from backend.models.schemas import AnswerExplanation, QueryUnderstanding, RetrievedChunk, RetrievedEvidence


def confidence_label(score: float) -> str:
    if score >= 0.72:
        return "high"
    if score >= 0.45:
        return "medium"
    return "low"


def retrieval_confidence(chunks: list[RetrievedChunk]) -> float:
    if not chunks:
        return 0.0
    best_final = max((chunk.final_score for chunk in chunks), default=0.0)
    top_chunks = chunks[:5]
    filenames = [chunk.metadata.filename for chunk in top_chunks]
    dominant_file_count = max((filenames.count(filename) for filename in set(filenames)), default=0)
    document_agreement = dominant_file_count / len(top_chunks) if top_chunks else 0.0
    average_final = sum(chunk.final_score for chunk in top_chunks) / len(top_chunks)

    confidence = (0.55 * best_final) + (0.25 * average_final) + (0.20 * document_agreement)
    return max(0.0, min(1.0, confidence))


def build_context_for_explanation(chunks: list[RetrievedChunk]) -> str:
    blocks = []
    for index, chunk in enumerate(chunks, start=1):
        page = f", Page {chunk.metadata.page_number}" if chunk.metadata.page_number else ""
        section = f", Section: {chunk.metadata.section_title}" if chunk.metadata.section_title else ""
        blocks.append(
            f"[{index}] {chunk.metadata.filename}{page}{section}\n"
            f"chunk_id={chunk.metadata.chunk_id}\n"
            f"{chunk.text}"
        )
    return "\n\n".join(blocks)


def build_explanation(
    query_understanding: QueryUnderstanding,
    chunks: list[RetrievedChunk],
) -> AnswerExplanation:
    evidence = [
        RetrievedEvidence(
            citation_number=index,
            filename=chunk.metadata.filename,
            page_number=chunk.metadata.page_number,
            section_title=chunk.metadata.section_title,
            chunk_id=chunk.metadata.chunk_id,
            text=chunk.text,
            vector_score=chunk.vector_score,
            keyword_score=chunk.keyword_score,
            final_score=chunk.final_score,
            rerank_score=chunk.rerank_score,
        )
        for index, chunk in enumerate(chunks, start=1)
    ]
    return AnswerExplanation(
        query_understanding=query_understanding,
        retrieved_chunks=evidence,
        context=build_context_for_explanation(chunks),
    )
