from backend.rag.chunker import chunk_pages
from backend.rag.parser import ParsedPage


def test_chunk_pages_preserves_metadata():
    pages = [ParsedPage(text="Policy\n\nEmployees receive annual leave. Carry forward is limited.", page_number=3, section_title="Policy")]

    chunks = chunk_pages(pages, document_id="doc-1", filename="handbook.txt")

    assert chunks
    assert chunks[0].metadata.document_id == "doc-1"
    assert chunks[0].metadata.filename == "handbook.txt"
    assert chunks[0].metadata.page_number == 3
    assert chunks[0].metadata.section_title == "Policy"


def test_chunk_pages_returns_empty_for_empty_pages():
    assert chunk_pages([], document_id="doc-1", filename="empty.txt") == []
