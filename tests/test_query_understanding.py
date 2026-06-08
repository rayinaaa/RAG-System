from backend.models.schemas import ChatMessage, ChunkMetadata, RetrievedChunk
from backend.rag.explainability import confidence_label, retrieval_confidence
from backend.rag.query_understanding import understand_query


def test_query_understanding_expands_abbreviations():
    understanding = understand_query("Explain the API decisions", [])

    assert understanding.query_type == "search"
    assert any("application programming interface" in query for query in understanding.expanded_queries)


def test_query_understanding_detects_follow_up():
    history = [ChatMessage(role="user", content="Summarize March activities")]

    understanding = understand_query("What skills improved from that?", history)

    assert understanding.query_type == "follow_up"
    assert any("Summarize March activities" in query for query in understanding.expanded_queries)


def test_confidence_label_thresholds():
    assert confidence_label(0.8) == "high"
    assert confidence_label(0.5) == "medium"
    assert confidence_label(0.2) == "low"


def test_retrieval_confidence_respects_document_agreement():
    chunks = [
        RetrievedChunk(
            text="resume chunk",
            metadata=ChunkMetadata(chunk_id=f"chunk-{index}", document_id="doc-1", filename="resume.pdf"),
            vector_score=0.5,
            final_score=0.35,
            rerank_score=-11,
        )
        for index in range(5)
    ]

    assert retrieval_confidence(chunks) >= 0.35
