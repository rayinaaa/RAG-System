from backend.models.schemas import RetrievedChunk, SourceCitation


def _preview(text: str, max_length: int = 240) -> str:
    compact = " ".join(text.split())
    if len(compact) <= max_length:
        return compact
    return f"{compact[: max_length - 3]}..."


def build_sources(chunks: list[RetrievedChunk]) -> list[SourceCitation]:
    sources: list[SourceCitation] = []
    for index, chunk in enumerate(chunks, start=1):
        chunk.citation_number = index
        sources.append(
            SourceCitation(
                number=index,
                filename=chunk.metadata.filename,
                page_number=chunk.metadata.page_number,
                section_title=chunk.metadata.section_title,
                chunk_id=chunk.metadata.chunk_id,
                preview=_preview(chunk.text),
                confidence=max(0.0, min(1.0, chunk.final_score)),
            )
        )
    return sources
