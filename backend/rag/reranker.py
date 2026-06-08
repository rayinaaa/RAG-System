from functools import cached_property

from backend.models.schemas import RetrievedChunk
from backend.services.config import settings


class Reranker:
    @cached_property
    def model(self):
        from sentence_transformers import CrossEncoder

        return CrossEncoder(
            settings.reranker_model,
            cache_dir=str(settings.model_cache_dir / "transformers"),
            local_files_only=True,
        )

    def rerank(self, query: str, chunks: list[RetrievedChunk], top_k: int = 5) -> list[RetrievedChunk]:
        if not chunks:
            return []
        pairs = [(query, chunk.text) for chunk in chunks]
        scores = self.model.predict(pairs).tolist()
        ranked: list[RetrievedChunk] = []
        for chunk, score in zip(chunks, scores):
            ranked.append(chunk.model_copy(update={"rerank_score": float(score)}))
        return sorted(ranked, key=lambda item: item.rerank_score or 0, reverse=True)[:top_k]


reranker = Reranker()
