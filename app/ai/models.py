"""LangChain chat-model factory.

All LangChain-based AI code (chains, agents) gets its model from here, so the
model/provider is configured in ONE place (Phase 12). Swap ChatOllama for
another provider's chat model later and nothing else changes.
"""

from __future__ import annotations

from langchain_ollama import ChatOllama

from app.core.config import settings


def get_chat_model(temperature: float | None = None, **kwargs) -> ChatOllama:
    """Return a configured ChatOllama instance pointed at our local model."""
    return ChatOllama(
        model=settings.LLM_MODEL,
        base_url=settings.OLLAMA_HOST,
        temperature=settings.LLM_TEMPERATURE if temperature is None else temperature,
        **kwargs,
    )
