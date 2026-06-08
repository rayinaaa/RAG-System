from backend.models.schemas import ChunkMetadata, RetrievedChunk
from backend.rag.retriever import _normalize, retriever


def test_normalize_handles_equal_zero_scores():
    assert _normalize([0, 0]) == [0.0, 0.0]


def test_hybrid_search_merges_vector_and_keyword(monkeypatch):
    metadata = ChunkMetadata(chunk_id="chunk-1", document_id="doc-1", filename="a.txt")
    vector = RetrievedChunk(text="annual leave policy", metadata=metadata, vector_score=0.8, final_score=0.8)
    keyword = RetrievedChunk(text="annual leave policy", metadata=metadata, keyword_score=0.5, final_score=0.5)

    monkeypatch.setattr(retriever, "vector_search", lambda query, top_k=20: [vector])
    monkeypatch.setattr(retriever, "keyword_search", lambda query, top_k=20: [keyword])

    results = retriever.hybrid_search("leave", top_k=20)

    assert len(results) == 1
    assert results[0].final_score == (0.7 * 0.8) + (0.3 * 0.5)


def test_hybrid_search_many_keeps_best_duplicate(monkeypatch):
    metadata = ChunkMetadata(chunk_id="chunk-1", document_id="doc-1", filename="a.txt")
    weaker = RetrievedChunk(text="api overview", metadata=metadata, final_score=0.2)
    stronger = RetrievedChunk(text="api overview", metadata=metadata, final_score=0.9)

    def fake_hybrid(query, top_k=20):
        return [weaker] if query == "api" else [stronger]

    monkeypatch.setattr(retriever, "hybrid_search", fake_hybrid)

    results = retriever.hybrid_search_many(["api", "application programming interface"])

    assert len(results) == 1
    assert results[0].final_score == 0.9
