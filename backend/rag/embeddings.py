from functools import cached_property

import chromadb

from backend.services.config import settings


class EmbeddingService:
    @cached_property
    def model(self):
        from sentence_transformers import SentenceTransformer

        return SentenceTransformer(
            settings.embedding_model,
            cache_folder=str(settings.model_cache_dir / "sentence_transformers"),
            local_files_only=False,
        )

    @cached_property
    def client(self):
        return chromadb.PersistentClient(path=str(settings.chroma_dir))

    @cached_property
    def collection(self):
        return self.client.get_or_create_collection(name="documents", metadata={"hnsw:space": "cosine"})

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return self.model.encode(
            texts,
            normalize_embeddings=True,
            batch_size=32,
            show_progress_bar=False,
        ).tolist()

    def delete_document(self, document_id: str) -> None:
        self.collection.delete(where={"document_id": document_id})


embeddings = EmbeddingService()
