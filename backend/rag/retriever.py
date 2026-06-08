import math
import re

from rank_bm25 import BM25Okapi

from backend.models.schemas import ChunkMetadata, RetrievedChunk
from backend.rag.embeddings import embeddings


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z0-9]+", text.lower())


def _normalize(scores: list[float]) -> list[float]:
    if not scores:
        return []
    low, high = min(scores), max(scores)
    if math.isclose(low, high):
        return [1.0 if score > 0 else 0.0 for score in scores]
    return [(score - low) / (high - low) for score in scores]


def _metadata_from_chroma(metadata: dict) -> ChunkMetadata:
    cleaned = dict(metadata)
    if cleaned.get("page_number") == "":
        cleaned["page_number"] = None
    if cleaned.get("section_title") == "":
        cleaned["section_title"] = None
    return ChunkMetadata(**cleaned)


class HybridRetriever:
    def _all_chunks(self) -> tuple[list[str], list[dict]]:
        try:
            data = embeddings.collection.get(include=["documents", "metadatas"])
            return data.get("documents", []), data.get("metadatas", [])
        except Exception:
            return [], []

    def vector_search(self, query: str, top_k: int = 20) -> list[RetrievedChunk]:
        try:
            if embeddings.collection.count() == 0:
                return []
        except Exception:
            return []
        try:
            query_embedding = embeddings.embed_texts([query])[0]
            result = embeddings.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=["documents", "metadatas", "distances"],
            )
        except Exception:
            return []
        chunks: list[RetrievedChunk] = []
        for text, metadata, distance in zip(
            result.get("documents", [[]])[0],
            result.get("metadatas", [[]])[0],
            result.get("distances", [[]])[0],
        ):
            vector_score = max(0.0, 1.0 - float(distance))
            chunks.append(
                RetrievedChunk(
                    text=text,
                    metadata=_metadata_from_chroma(metadata),
                    vector_score=vector_score,
                    final_score=vector_score,
                )
            )
        return chunks

    def keyword_search(self, query: str, top_k: int = 20) -> list[RetrievedChunk]:
        docs, metadatas = self._all_chunks()
        if not docs:
            return []
        bm25 = BM25Okapi([_tokenize(doc) for doc in docs])
        raw_scores = bm25.get_scores(_tokenize(query)).tolist()
        normalized = _normalize(raw_scores)
        ranked = sorted(enumerate(normalized), key=lambda item: item[1], reverse=True)[:top_k]
        return [
            RetrievedChunk(
                text=docs[index],
                metadata=_metadata_from_chroma(metadatas[index]),
                keyword_score=score,
                final_score=score,
            )
            for index, score in ranked
            if score > 0
        ]

    def hybrid_search(self, query: str, top_k: int = 20) -> list[RetrievedChunk]:
        vector_results = {item.metadata.chunk_id: item for item in self.vector_search(query, top_k=top_k)}
        keyword_results = {item.metadata.chunk_id: item for item in self.keyword_search(query, top_k=top_k)}
        all_ids = set(vector_results) | set(keyword_results)
        merged: list[RetrievedChunk] = []

        for chunk_id in all_ids:
            vector = vector_results.get(chunk_id)
            keyword = keyword_results.get(chunk_id)
            base = vector or keyword
            vector_score = vector.vector_score if vector else 0
            keyword_score = keyword.keyword_score if keyword else 0
            merged.append(
                RetrievedChunk(
                    text=base.text,
                    metadata=base.metadata,
                    vector_score=vector_score,
                    keyword_score=keyword_score,
                    final_score=(0.7 * vector_score) + (0.3 * keyword_score),
                )
            )

        return sorted(merged, key=lambda item: item.final_score, reverse=True)[:top_k]

    def hybrid_search_many(self, queries: list[str], top_k: int = 20) -> list[RetrievedChunk]:
        merged: dict[str, RetrievedChunk] = {}
        for query in queries:
            for chunk in self.hybrid_search(query, top_k=top_k):
                existing = merged.get(chunk.metadata.chunk_id)
                if existing is None or chunk.final_score > existing.final_score:
                    merged[chunk.metadata.chunk_id] = chunk
        return sorted(merged.values(), key=lambda item: item.final_score, reverse=True)[:top_k]

retriever = HybridRetriever()
