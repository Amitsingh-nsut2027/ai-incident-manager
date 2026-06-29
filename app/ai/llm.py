"""Thin, swappable wrapper around the local Ollama LLM.

ALL AI calls go through here. If we ever switch models or providers, this is the
only file that changes — the agents don't care what's behind it (good design).
"""

from __future__ import annotations

import json

import ollama

from app.core.config import settings

# A client pointed at our local Ollama server (localhost:11434 by default).
_client = ollama.Client(host=settings.OLLAMA_HOST)


def chat(
    prompt: str,
    system: str | None = None,
    model: str | None = None,
    temperature: float | None = None,
) -> str:
    """Send a prompt to the LLM and return its text reply."""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    response = _client.chat(
        model=model or settings.LLM_MODEL,
        messages=messages,
        options={"temperature": settings.LLM_TEMPERATURE if temperature is None else temperature},
    )
    return response["message"]["content"]


def chat_json(
    prompt: str,
    system: str | None = None,
    model: str | None = None,
    temperature: float | None = None,
) -> dict:
    """Like chat(), but forces the model to return valid JSON and parses it.

    Uses Ollama's `format="json"` mode. This is what the agents use to get
    structured, machine-readable output instead of chatty prose.
    """
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    response = _client.chat(
        model=model or settings.LLM_MODEL,
        messages=messages,
        format="json",
        options={"temperature": settings.LLM_TEMPERATURE if temperature is None else temperature},
    )
    return json.loads(response["message"]["content"])


def is_available() -> bool:
    """Return True if the Ollama server is reachable (for health checks)."""
    try:
        _client.list()
        return True
    except Exception:
        return False
