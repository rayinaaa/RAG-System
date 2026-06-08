from typing import AsyncIterator

import httpx

from backend.services.config import settings


class GeminiClient:
    def _api_key(self) -> str:
        api_key = (settings.gemini_api_key or "").strip()
        if not api_key or api_key == "paste-your-gemini-api-key-here":
            raise RuntimeError("GEMINI_API_KEY is not configured")
        return api_key

    def _url(self) -> str:
        return (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{settings.gemini_model}:generateContent"
        )

    def _payload(self, prompt: str) -> dict:
        return {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": settings.llm_temperature,
                "topP": 0.8,
            },
        }

    async def generate(self, prompt: str) -> str:
        timeout = httpx.Timeout(settings.llm_timeout_seconds)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                self._url(),
                params={"key": self._api_key()},
                json=self._payload(prompt),
            )

        if response.status_code >= 400:
            detail = self._error_detail(response)
            raise RuntimeError(detail)

        data = response.json()
        candidates = data.get("candidates") or []
        if not candidates:
            return "Information not found in uploaded documents."

        parts = candidates[0].get("content", {}).get("parts", [])
        answer = "".join(part.get("text", "") for part in parts).strip()
        return answer or "Information not found in uploaded documents."

    async def stream(self, prompt: str) -> AsyncIterator[str]:
        # Use one bounded REST call and emit the final answer as a single SSE token.
        # This avoids the Gemini SDK hanging on some Windows/network setups.
        yield await self.generate(prompt)

    @staticmethod
    def _error_detail(response: httpx.Response) -> str:
        try:
            payload = response.json()
        except ValueError:
            return f"Gemini request failed with HTTP {response.status_code}: {response.text}"

        error = payload.get("error") or {}
        message = error.get("message") or response.text
        status = error.get("status")
        if status:
            return f"Gemini {status}: {message}"
        return f"Gemini request failed with HTTP {response.status_code}: {message}"


llm_client = GeminiClient()
