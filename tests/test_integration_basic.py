from backend.rag.prompt_builder import build_prompt
from backend.models.schemas import ChunkMetadata, RetrievedChunk


def test_prompt_contains_context_and_query():
    chunk = RetrievedChunk(
        text="Employees receive 12 annual leaves.",
        metadata=ChunkMetadata(chunk_id="c1", document_id="d1", filename="policy.txt", page_number=1),
    )

    prompt = build_prompt("How many leaves?", [chunk], [])

    assert "Employees receive 12 annual leaves." in prompt
    assert "How many leaves?" in prompt
    assert "policy.txt" in prompt
