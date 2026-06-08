import asyncio
import json
from pathlib import Path
from threading import Lock
from typing import Any

from backend.models.schemas import DocumentRecord
from backend.services.config import settings


class DocumentStorage:
    def __init__(self, path: Path):
        self.path = path
        self._lock = Lock()
        self._subscriber_lock = Lock()
        self._documents: dict[str, DocumentRecord] = {}
        self._subscribers: list[tuple[asyncio.AbstractEventLoop, asyncio.Queue[dict[str, Any]]]] = []

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists():
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            self._documents = {item["id"]: DocumentRecord(**item) for item in raw}

    def _persist(self) -> None:
        self.path.write_text(
            json.dumps([doc.model_dump(mode="json") for doc in self._documents.values()], indent=2),
            encoding="utf-8",
        )

    def _payload(self, event: str) -> dict[str, Any]:
        return {
            "event": event,
            "documents": [doc.model_dump(mode="json") for doc in self.list_documents()],
        }

    def _publish(self, event: str) -> None:
        payload = self._payload(event)
        stale: list[tuple[asyncio.AbstractEventLoop, asyncio.Queue[dict[str, Any]]]] = []
        with self._subscriber_lock:
            subscribers = list(self._subscribers)

        for loop, queue in subscribers:
            if loop.is_closed():
                stale.append((loop, queue))
                continue
            loop.call_soon_threadsafe(queue.put_nowait, payload)

        for subscriber in stale:
            with self._subscriber_lock:
                if subscriber in self._subscribers:
                    self._subscribers.remove(subscriber)

    def subscribe(self) -> asyncio.Queue[dict[str, Any]]:
        loop = asyncio.get_running_loop()
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        subscriber = (loop, queue)
        with self._subscriber_lock:
            self._subscribers.append(subscriber)
        queue.put_nowait(self._payload("snapshot"))
        return queue

    def unsubscribe(self, queue: asyncio.Queue[dict[str, Any]]) -> None:
        with self._subscriber_lock:
            self._subscribers = [subscriber for subscriber in self._subscribers if subscriber[1] is not queue]

    def add_document(self, record: DocumentRecord) -> None:
        with self._lock:
            self._documents[record.id] = record
            self._persist()
        self._publish("document_added")

    def update_document(self, document_id: str, **changes) -> None:
        with self._lock:
            record = self._documents[document_id]
            self._documents[document_id] = record.model_copy(update=changes)
            self._persist()
        self._publish("document_updated")

    def get_document(self, document_id: str) -> DocumentRecord | None:
        with self._lock:
            return self._documents.get(document_id)

    def list_documents(self) -> list[DocumentRecord]:
        with self._lock:
            return sorted(self._documents.values(), key=lambda item: item.created_at, reverse=True)

    def delete_document(self, document_id: str) -> None:
        with self._lock:
            record = self._documents.pop(document_id, None)
            if record:
                Path(record.path).unlink(missing_ok=True)
            self._persist()
        self._publish("document_deleted")


storage = DocumentStorage(settings.metadata_path)
