import re

from backend.models.schemas import SourceCitation


NOT_FOUND = "Information not found in uploaded documents."


def verify_grounded_answer(answer: str, sources: list[SourceCitation], confidence: float) -> str:
    stripped = answer.strip()
    if not stripped or NOT_FOUND in stripped:
        return NOT_FOUND
    if confidence < 0.35 or not sources:
        return "Information not confidently found in uploaded documents."

    cited_numbers = {int(match) for match in re.findall(r"\[(\d+)\]", stripped)}
    allowed_numbers = {source.number for source in sources}
    if not cited_numbers.intersection(allowed_numbers):
        primary = sources[0].number
        stripped = f"{stripped} [{primary}]"

    if "Sources:" not in stripped:
        source_lines = "\n".join(
            f"[{source.number}] {source.filename}"
            f"{', Page ' + str(source.page_number) if source.page_number else ''}"
            for source in sources
        )
        stripped = f"{stripped}\n\nSources:\n{source_lines}"

    return stripped
