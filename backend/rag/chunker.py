import re
from uuid import uuid4

from backend.models.schemas import ChunkMetadata, TextChunk
from backend.rag.parser import ParsedPage, clean_text
from backend.services.config import settings


def _split_paragraphs(text: str) -> list[str]:
    parts = re.split(r"\n\s*\n", text)
    expanded: list[str] = []
    for part in parts:
        part = clean_text(part)
        if not part:
            continue
        if len(part) > settings.chunk_size * 1.5:
            expanded.extend([segment.strip() for segment in re.split(r"(?<=[.!?])\s+", part) if segment.strip()])
        else:
            expanded.append(part)
    return expanded


def _window_text(text: str, size: int, overlap: int) -> list[str]:
    if len(text) <= size:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        chunks.append(text[start:end].strip())
        if end == len(text):
            break
        start = max(0, end - overlap)
    return [chunk for chunk in chunks if chunk]


def chunk_pages(pages: list[ParsedPage], document_id: str, filename: str) -> list[TextChunk]:
    chunks: list[TextChunk] = []
    for page in pages:
        paragraphs = _split_paragraphs(page.text)
        buffer = ""
        for paragraph in paragraphs:
            candidate = f"{buffer}\n\n{paragraph}".strip() if buffer else paragraph
            if len(candidate) <= settings.chunk_size:
                buffer = candidate
                continue

            if buffer:
                for text in _window_text(buffer, settings.chunk_size, settings.chunk_overlap):
                    chunks.append(
                        TextChunk(
                            text=text,
                            metadata=ChunkMetadata(
                                chunk_id=str(uuid4()),
                                document_id=document_id,
                                filename=filename,
                                page_number=page.page_number,
                                section_title=page.section_title,
                            ),
                        )
                    )
            buffer = paragraph

        if buffer:
            for text in _window_text(buffer, settings.chunk_size, settings.chunk_overlap):
                chunks.append(
                    TextChunk(
                        text=text,
                        metadata=ChunkMetadata(
                            chunk_id=str(uuid4()),
                            document_id=document_id,
                            filename=filename,
                            page_number=page.page_number,
                            section_title=page.section_title,
                        ),
                    )
                )
    return chunks

