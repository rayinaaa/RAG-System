import asyncio
import json
from typing import AsyncIterator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from backend.models.schemas import DocumentSummaryResponse
from backend.rag.document_insights import (
    build_action_items,
    build_document_summary,
    build_important_dates,
    build_key_topics,
    build_suggested_questions,
)
from backend.rag.embeddings import embeddings
from backend.services.storage import storage

router = APIRouter(tags=["documents"])


@router.get("/documents")
def list_documents():
    return storage.list_documents()


@router.get("/documents/{document_id}/summary", response_model=DocumentSummaryResponse)
def document_summary(document_id: str):
    record = storage.get_document(document_id)
    if not record:
        raise HTTPException(status_code=404, detail="Document not found")
    if record.status != "ready":
        raise HTTPException(status_code=409, detail="Document is not ready for summary generation yet")

    return DocumentSummaryResponse(
        document_id=document_id,
        filename=record.filename,
        summary=build_document_summary(document_id),
        suggested_questions=build_suggested_questions(document_id),
        key_topics=build_key_topics(document_id),
        important_dates=build_important_dates(document_id),
        action_items=build_action_items(document_id),
    )


@router.get("/documents/events")
async def document_events():
    async def events() -> AsyncIterator[str]:
        queue = storage.subscribe()
        try:
            while True:
                try:
                    payload = await asyncio.wait_for(queue.get(), timeout=25)
                    yield f"event: {payload['event']}\ndata: {json.dumps(payload)}\n\n"
                except asyncio.TimeoutError:
                    yield "event: ping\ndata: {}\n\n"
        finally:
            storage.unsubscribe(queue)

    return StreamingResponse(events(), media_type="text/event-stream")


@router.delete("/documents/{document_id}")
def delete_document(document_id: str):
    record = storage.get_document(document_id)
    if not record:
        raise HTTPException(status_code=404, detail="Document not found")

    embeddings.delete_document(document_id)
    storage.delete_document(document_id)
    return {"deleted": True, "id": document_id}
