import logging
import shutil
import uuid
from pathlib import Path
from typing import List

from fastapi import APIRouter, File, HTTPException, UploadFile

from backend.models.schemas import DocumentRecord
from backend.rag.chunker import chunk_pages
from backend.rag.embeddings import embeddings
from backend.rag.parser import parse_document
from backend.services.config import settings
from backend.services.indexing import indexing_executor
from backend.services.storage import storage

logger = logging.getLogger(__name__)
router = APIRouter(tags=["documents"])


def _chroma_metadata(metadata: dict) -> dict[str, str | int | float | bool]:
    normalized: dict[str, str | int | float | bool] = {}
    for key, value in metadata.items():
        if value is None:
            normalized[key] = ""
        elif isinstance(value, (str, int, float, bool)):
            normalized[key] = value
        else:
            normalized[key] = str(value)
    return normalized


def _safe_filename(filename: str) -> str:
    clean = Path(filename).name.replace("\x00", "")
    if not clean:
        raise HTTPException(status_code=400, detail="Invalid filename")
    suffix = Path(clean).suffix.lower()
    if suffix not in settings.supported_extensions:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {suffix}")
    return clean


def _validate_upload(file: UploadFile, filename: str) -> None:
    if file.size and file.size > settings.max_upload_size_mb * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail=f"{filename} is too large. Maximum size is {settings.max_upload_size_mb} MB.",
        )


def process_document(document_id: str) -> None:
    record = storage.get_document(document_id)
    if not record:
        logger.warning("Document %s disappeared before processing", document_id)
        return

    try:
        storage.update_document(document_id, status="processing", progress=15)
        pages = parse_document(Path(record.path), record.filename)
        if not pages:
            raise ValueError("No readable text was found in this document.")
        storage.update_document(document_id, progress=45)
        chunks = chunk_pages(pages, document_id=document_id, filename=record.filename)
        if not chunks:
            raise ValueError("No indexable text chunks were produced from this document.")
        storage.update_document(document_id, progress=65)

        if chunks:
            vectors = embeddings.embed_texts([chunk.text for chunk in chunks])
            embeddings.collection.add(
                ids=[chunk.metadata.chunk_id for chunk in chunks],
                documents=[chunk.text for chunk in chunks],
                metadatas=[_chroma_metadata(chunk.metadata.model_dump()) for chunk in chunks],
                embeddings=vectors,
            )

        storage.update_document(
            document_id,
            status="ready",
            progress=100,
            chunk_count=len(chunks),
            error=None,
        )
        logger.info("Processed %s into %s chunks", record.filename, len(chunks))
    except Exception as exc:
        logger.exception("Failed processing %s", record.filename)
        storage.update_document(document_id, status="failed", progress=100, error=str(exc))


@router.post("/upload", response_model=List[DocumentRecord])
async def upload_documents(files: List[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")
    if len(files) > settings.max_upload_files:
        raise HTTPException(status_code=400, detail=f"Upload at most {settings.max_upload_files} files at once.")

    created: list[DocumentRecord] = []
    settings.upload_dir.mkdir(parents=True, exist_ok=True)

    for file in files:
        original_name = _safe_filename(file.filename or "")
        _validate_upload(file, original_name)
        document_id = str(uuid.uuid4())
        stored_name = f"{document_id}{Path(original_name).suffix.lower()}"
        destination = settings.upload_dir / stored_name

        with destination.open("wb") as out:
            shutil.copyfileobj(file.file, out)

        record = DocumentRecord(
            id=document_id,
            filename=original_name,
            path=str(destination),
            status="queued",
            progress=5,
            chunk_count=0,
        )
        storage.add_document(record)
        indexing_executor.submit(process_document, document_id)
        created.append(record)

    return created
