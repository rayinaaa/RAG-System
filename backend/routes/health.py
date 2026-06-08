from fastapi import APIRouter

from backend.services.config import settings
from backend.services.metrics import metrics

router = APIRouter(tags=["system"])


@router.get("/health")
def health_check():
    return {
        "status": "ok",
        "llm_provider": "gemini",
        "llm_model": settings.gemini_model,
        "metrics": metrics.snapshot(),
    }
