"""LangChain chat-model factory (Phase 12 + cloud deploy).

Returns a chat model based on LLM_PROVIDER:
  - "ollama" → local, free model on your machine (default for dev)
  - "groq"   → free hosted LLM API (for cloud deployment, no local GPU needed)
All AI code goes through here, so switching providers is a one-config change.
"""

from __future__ import annotations

from app.core.config import settings


def get_chat_model(temperature: float | None = None, **kwargs):
    """Return a configured chat model for the active provider."""
    temp = settings.LLM_TEMPERATURE if temperature is None else temperature

    if settings.LLM_PROVIDER == "groq":
        from langchain_groq import ChatGroq

        return ChatGroq(
            model=settings.GROQ_MODEL,
            api_key=settings.GROQ_API_KEY,
            temperature=temp,
            **kwargs,
        )

    # default: local Ollama
    from langchain_ollama import ChatOllama

    return ChatOllama(
        model=settings.LLM_MODEL,
        base_url=settings.OLLAMA_HOST,
        temperature=temp,
        **kwargs,
    )
