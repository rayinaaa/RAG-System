import pytest

from backend.services.llm import GeminiClient


def test_gemini_client_rejects_missing_api_key(monkeypatch):
    monkeypatch.setattr("backend.services.llm.settings.gemini_api_key", None)

    client = GeminiClient()

    with pytest.raises(RuntimeError, match="GEMINI_API_KEY is not configured"):
        client._api_key()


def test_gemini_client_rejects_placeholder_api_key(monkeypatch):
    monkeypatch.setattr("backend.services.llm.settings.gemini_api_key", "paste-your-gemini-api-key-here")

    client = GeminiClient()

    with pytest.raises(RuntimeError, match="GEMINI_API_KEY is not configured"):
        client._api_key()
