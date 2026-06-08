import json
import logging
import time
from typing import AsyncIterator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from backend.models.schemas import ChatRequest, ChatResponse, SourceCitation
from backend.rag.answer_verifier import verify_grounded_answer
from backend.rag.citation_builder import build_sources
from backend.rag.explainability import build_explanation, confidence_label, retrieval_confidence
from backend.rag.prompt_builder import build_prompt
from backend.rag.query_understanding import understand_query
from backend.rag.reranker import reranker
from backend.rag.retriever import retriever
from backend.services.llm import llm_client
from backend.services.metrics import metrics
from backend.services.sessions import sessions

logger = logging.getLogger(__name__)
router = APIRouter(tags=["chat"])


def _prepare_context(request: ChatRequest):
    started_retrieval = time.perf_counter()
    history = sessions.get_history(request.session_id)
    query_understanding = understand_query(request.message, history)
    hybrid_results = retriever.hybrid_search_many(query_understanding.expanded_queries, top_k=20)
    ranked_results = reranker.rerank(request.message, hybrid_results, top_k=5)
    retrieval_ms = (time.perf_counter() - started_retrieval) * 1000

    sources = build_sources(ranked_results)
    prompt = build_prompt(request.message, ranked_results, history)
    explanation = build_explanation(query_understanding, ranked_results)
    return ranked_results, sources, prompt, retrieval_ms, explanation


def _friendly_llm_error(exc: Exception) -> str:
    message = str(exc)
    lower_message = message.lower()
    if "429" in message or "quota" in lower_message or "rate limit" in lower_message:
        return (
            "Gemini quota exceeded for the configured model. "
            "Wait for the quota window to reset, use another Gemini model, or enable billing in Google AI Studio."
        )
    if "api key not valid" in lower_message or "api_key_invalid" in lower_message:
        return "Gemini rejected the API key. Copy the API key from Google AI Studio > Get API key, paste it into GEMINI_API_KEY, and restart the backend."
    if "api key" in lower_message:
        return "Gemini API key is missing or invalid. Check GEMINI_API_KEY in your .env file and restart the backend."
    if "timed out" in lower_message or "timeout" in lower_message:
        return "Gemini request timed out. Check your internet connection and try again."
    return "The AI model request failed. Please check the backend logs and try again."


def _finalize_response(
    request: ChatRequest,
    answer: str,
    sources: list[SourceCitation],
    ranked_results,
    retrieval_ms: float,
    generation_ms: float,
    explanation,
) -> ChatResponse:
    if "Information not found in uploaded documents." in answer:
        sources = []

    confidence = retrieval_confidence(ranked_results)
    answer = verify_grounded_answer(answer, sources, confidence)
    if "Information not confidently found in uploaded documents." in answer:
        sources = []
    sessions.append(request.session_id, "user", request.message)
    sessions.append(request.session_id, "assistant", answer)
    metrics.record_query(retrieval_ms=retrieval_ms, generation_ms=generation_ms, confidence=confidence)

    return ChatResponse(
        session_id=request.session_id,
        answer=answer,
        sources=sources,
        retrieval_ms=retrieval_ms,
        generation_ms=generation_ms,
        confidence=confidence,
        confidence_label=confidence_label(confidence),
        explanation=explanation,
    )


async def _generate_answer(request: ChatRequest) -> ChatResponse:
    ranked_results, sources, prompt, retrieval_ms, explanation = _prepare_context(request)
    started_generation = time.perf_counter()
    if not ranked_results:
        answer = "Information not found in uploaded documents."
    else:
        answer = await llm_client.generate(prompt)
    generation_ms = (time.perf_counter() - started_generation) * 1000

    return _finalize_response(request, answer, sources, ranked_results, retrieval_ms, generation_ms, explanation)


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message is required")
    try:
        return await _generate_answer(request)
    except Exception as exc:
        logger.exception("Chat request failed")
        raise HTTPException(status_code=502, detail=_friendly_llm_error(exc)) from exc


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message is required")

    async def events() -> AsyncIterator[str]:
        try:
            ranked_results, sources, prompt, retrieval_ms, explanation = _prepare_context(request)
            yield f"data: {json.dumps({'type': 'retrieval_done', 'retrieval_ms': retrieval_ms})}\n\n"

            started_generation = time.perf_counter()
            if not ranked_results:
                answer = "Information not found in uploaded documents."
                yield f"data: {json.dumps({'type': 'token', 'token': answer})}\n\n"
            else:
                tokens: list[str] = []
                async for token in llm_client.stream(prompt):
                    tokens.append(token)
                    yield f"data: {json.dumps({'type': 'token', 'token': token})}\n\n"
                answer = "".join(tokens).strip() or "Information not found in uploaded documents."

            generation_ms = (time.perf_counter() - started_generation) * 1000
            response = _finalize_response(request, answer, sources, ranked_results, retrieval_ms, generation_ms, explanation)
            yield f"data: {json.dumps({'type': 'done', 'payload': response.model_dump()})}\n\n"
        except Exception as exc:
            logger.exception("Streaming chat failed")
            yield f"data: {json.dumps({'type': 'error', 'error': _friendly_llm_error(exc)})}\n\n"

    return StreamingResponse(events(), media_type="text/event-stream")
