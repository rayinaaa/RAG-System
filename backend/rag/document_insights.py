import re

from backend.rag.embeddings import embeddings


def _sentences(text: str) -> list[str]:
    return [item.strip() for item in re.split(r"(?<=[.!?])\s+", text) if item.strip()]


def _document_chunks(document_id: str, limit: int = 8) -> list[str]:
    data = embeddings.collection.get(where={"document_id": document_id}, include=["documents"], limit=limit)
    return data.get("documents", [])


def _document_text(document_id: str, limit: int = 12) -> str:
    return " ".join(_document_chunks(document_id, limit=limit))


def build_document_summary(document_id: str) -> str:
    chunks = _document_chunks(document_id)
    if not chunks:
        return "No indexed text is available for this document yet."

    candidate_sentences: list[str] = []
    for chunk in chunks[:5]:
        candidate_sentences.extend(_sentences(chunk))
    summary = " ".join(candidate_sentences[:4]).strip()
    return summary or "No concise summary could be generated from the indexed text."


def build_suggested_questions(document_id: str) -> list[str]:
    chunks = _document_chunks(document_id, limit=5)
    text = " ".join(chunks).lower()
    questions = ["What are the main points in this document?"]

    if any(term in text for term in ("policy", "procedure", "must", "required")):
        questions.append("What requirements or policies are described?")
    if any(term in text for term in ("date", "deadline", "effective", "expires")):
        questions.append("Are there important dates or deadlines?")
    if any(term in text for term in ("cost", "price", "amount", "total", "budget")):
        questions.append("What financial amounts are mentioned?")
    if any(term in text for term in ("risk", "issue", "exception", "failure")):
        questions.append("What risks or exceptions are mentioned?")

    questions.append("Which sections should I review first?")
    return questions[:5]


def build_key_topics(document_id: str) -> list[str]:
    text = _document_text(document_id).lower()
    candidates = {
        "requirements": ("require", "must", "shall", "policy"),
        "timeline": ("date", "deadline", "schedule", "milestone"),
        "financials": ("budget", "cost", "price", "amount", "revenue"),
        "risks": ("risk", "issue", "blocked", "failure", "exception"),
        "people": ("team", "employee", "stakeholder", "manager", "client"),
        "deliverables": ("deliverable", "task", "action", "submission", "report"),
    }
    topics = [label.title() for label, terms in candidates.items() if any(term in text for term in terms)]
    return topics[:6] or ["General document overview"]


def build_important_dates(document_id: str) -> list[str]:
    text = _document_text(document_id)
    patterns = [
        r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
        r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{2,4}\b",
        r"\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.?\s+\d{2,4}\b",
    ]
    found: list[str] = []
    for pattern in patterns:
        found.extend(re.findall(pattern, text, flags=re.IGNORECASE))
    deduped = []
    for item in found:
        compact = " ".join(item.split())
        if compact not in deduped:
            deduped.append(compact)
    return deduped[:8]


def build_action_items(document_id: str) -> list[str]:
    sentences = _sentences(_document_text(document_id))
    action_terms = ("must", "should", "need to", "required", "action", "submit", "complete", "review")
    items = [sentence for sentence in sentences if any(term in sentence.lower() for term in action_terms)]
    return items[:5]
