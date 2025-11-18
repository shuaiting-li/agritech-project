"""LLM client abstractions."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from .config import Settings, get_settings

logger = logging.getLogger(__name__)


class BaseLLMClient:
    def generate(self, prompt: str, temperature: float = 0.2) -> str:  # pragma: no cover - interface
        raise NotImplementedError


class OfflineLLMClient(BaseLLMClient):
    """Deterministic placeholder used for local development."""

    def generate(self, prompt: str, temperature: float = 0.2) -> str:
        guidance = "\n".join(line for line in prompt.splitlines()[-8:])
        return (
            "[offline stub] Based on the available agritech notes I suggest: "
            f"{guidance[:400]}..."
        )


class GeminiTextClient(BaseLLMClient):
    def __init__(self, api_key: str, model: str) -> None:
        try:
            import google.generativeai as genai
        except ImportError as exc:  # pragma: no cover - dependency guard
            raise RuntimeError("google-generativeai package missing") from exc

        if not api_key:
            raise ValueError("GEMINI_API_KEY is required")

        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel(model)

    def generate(self, prompt: str, temperature: float = 0.2) -> str:
        response = self._model.generate_content(
            prompt,
            generation_config={"temperature": temperature, "top_p": 0.8, "top_k": 40},
        )
        if not response.candidates:
            return "I could not produce a response."
        return response.text.strip()


@dataclass(slots=True)
class LLMFactory:
    settings: Settings

    def create(self) -> BaseLLMClient:
        if self.settings.offline_mode():
            logger.warning("Using OfflineLLMClient because Gemini credentials are missing or disabled")
            return OfflineLLMClient()
        return GeminiTextClient(
            api_key=self.settings.gemini_api_key or "",
            model=self.settings.llm_model,
        )


def build_llm(settings: Settings | None = None) -> BaseLLMClient:
    return LLMFactory(settings or get_settings()).create()
