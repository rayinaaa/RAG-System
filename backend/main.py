from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.routes import chat, documents, health, upload
from backend.services.config import settings
from backend.services.logging_config import configure_logging
from backend.services.storage import storage


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    storage.initialize()
    yield


app = FastAPI(
    title="AI Document Chat Assistant",
    description="Production-ready Retrieval-Augmented Generation API for document chat.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(upload.router)
app.include_router(documents.router)
app.include_router(chat.router)

app.mount("/uploads", StaticFiles(directory=str(settings.upload_dir)), name="uploads")

