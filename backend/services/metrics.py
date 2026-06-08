import json
from pathlib import Path
from threading import Lock

from backend.services.config import settings
from backend.services.storage import storage


class MetricsStore:
    def __init__(self, path: Path):
        self.path = path
        self._lock = Lock()
        self.query_count = 0
        self.total_retrieval_ms = 0.0
        self.total_generation_ms = 0.0
        self.total_confidence = 0.0
        self.successful_retrievals = 0
        self._load()

    def _load(self) -> None:
        if self.path.exists():
            data = json.loads(self.path.read_text(encoding="utf-8"))
            self.query_count = int(data.get("query_count", 0))
            self.total_retrieval_ms = float(data.get("total_retrieval_ms", 0))
            self.total_generation_ms = float(data.get("total_generation_ms", 0))
            self.total_confidence = float(data.get("total_confidence", 0))
            self.successful_retrievals = int(data.get("successful_retrievals", 0))

    def _persist(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(
                {
                    "query_count": self.query_count,
                    "total_retrieval_ms": self.total_retrieval_ms,
                    "total_generation_ms": self.total_generation_ms,
                    "total_confidence": self.total_confidence,
                    "successful_retrievals": self.successful_retrievals,
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    def record_query(self, retrieval_ms: float, generation_ms: float, confidence: float) -> None:
        with self._lock:
            self.query_count += 1
            self.total_retrieval_ms += retrieval_ms
            self.total_generation_ms += generation_ms
            self.total_confidence += confidence
            if confidence >= 0.35:
                self.successful_retrievals += 1
            self._persist()

    def snapshot(self) -> dict:
        documents = storage.list_documents()
        total_chunks = sum(doc.chunk_count for doc in documents)
        return {
            "total_documents": len(documents),
            "total_chunks": total_chunks,
            "average_retrieval_time_ms": self.total_retrieval_ms / self.query_count if self.query_count else 0,
            "average_generation_time_ms": self.total_generation_ms / self.query_count if self.query_count else 0,
            "average_confidence": self.total_confidence / self.query_count if self.query_count else 0,
            "retrieval_success_rate": self.successful_retrievals / self.query_count if self.query_count else 0,
            "total_queries_processed": self.query_count,
        }


metrics = MetricsStore(settings.metrics_path)
