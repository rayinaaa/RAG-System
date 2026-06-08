import re

from backend.models.schemas import ChatMessage, QueryUnderstanding


SUMMARY_TERMS = {"summarize", "summary", "overview", "main points", "key points"}
COMPARISON_TERMS = {"compare", "versus", " vs ", "difference", "differences", "similarities"}
FOLLOW_UP_TERMS = {"they", "it", "that", "those", "these", "he", "she", "them", "their"}

ABBREVIATIONS = {
    "pm": "project management product management",
    "api": "application programming interface",
    "ui": "user interface",
    "ux": "user experience",
    "rag": "retrieval augmented generation",
    "llm": "large language model",
    "kpi": "key performance indicator",
    "roi": "return on investment",
}


def classify_query(query: str, history: list[ChatMessage]) -> str:
    normalized = f" {query.lower().strip()} "
    if history and any(re.search(rf"\b{term}\b", normalized) for term in FOLLOW_UP_TERMS):
        return "follow_up"
    if any(term in normalized for term in COMPARISON_TERMS):
        return "comparison"
    if any(term in normalized for term in SUMMARY_TERMS):
        return "summary"
    return "search"


def expand_query(query: str, history: list[ChatMessage]) -> list[str]:
    normalized = query.lower()
    expanded = [query.strip()]

    for abbreviation, expansion in ABBREVIATIONS.items():
        if re.search(rf"\b{re.escape(abbreviation)}\b", normalized):
            expanded.append(f"{query} {expansion}")

    if history and classify_query(query, history) == "follow_up":
        recent_user_turns = [message.content for message in history[-4:] if message.role == "user"]
        if recent_user_turns:
            expanded.append(f"{recent_user_turns[-1]} {query}")

    deduped: list[str] = []
    for item in expanded:
        compact = " ".join(item.split())
        if compact and compact.lower() not in {existing.lower() for existing in deduped}:
            deduped.append(compact)
    return deduped[:3]


def understand_query(query: str, history: list[ChatMessage]) -> QueryUnderstanding:
    query_type = classify_query(query, history)
    expanded_queries = expand_query(query, history)
    rationale = {
        "summary": "Summary intent detected from summarization language.",
        "comparison": "Comparison intent detected from contrast language.",
        "follow_up": "Follow-up intent detected from pronouns and existing chat history.",
        "search": "Direct search intent detected.",
    }[query_type]
    return QueryUnderstanding(query_type=query_type, expanded_queries=expanded_queries, rationale=rationale)
